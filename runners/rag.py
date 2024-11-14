import os
import getpass
import io
from pprint import pprint
from typing import List
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from PIL import Image

from langchain import hub
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma

from langgraph.graph import START, END, StateGraph

# Custom
from cwe_parser import load_cwe_from_xml
from prompts import *

# Self-RAG
# https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# LOGIN
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

load_dotenv()

def _set_env(key: str):
    if key not in os.environ:
        os.environ[key] = getpass.getpass(f"{key}:")


_set_env("ANTHROPIC_API_KEY")
_set_env("OPENAI_API_KEY")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# PARSE SOURCES CREATE KB WITH RETRIEVER
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def getDocChunks():
    # Load documents from XML
    docs = load_cwe_from_xml(os.getenv('CWE_SRC'))

    # Split documents into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=250, chunk_overlap=0
    )
    doc_splits = text_splitter.split_documents(docs)

    return doc_splits

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CREATE KB WITH RETRIEVER
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Define the persist directory path
persist_directory = os.getenv('RAG_PERSIST')

# Check if vectorstore already exists
if os.listdir(persist_directory):
    # Load existing vectorstore
    vectorstore = Chroma(
        collection_name="TOOLRAG",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=persist_directory
    )
    print("Loaded existing vectorstore.")
else:
    # Vectorstore doesn't exist, create it and add documents
    vectorstore = Chroma.from_documents(
        documents=getDocChunks(),  # Ensure this function provides the document chunks
        collection_name="TOOLRAG",
        embedding=OpenAIEmbeddings(),
        persist_directory=persist_directory
    )
    print("Created new vectorstore and added documents.")
# Document Retriever
retriever = vectorstore.as_retriever()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# MODEL(S)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# LLM
if os.getenv('MODEL_SRC') == 'ANTHROPIC':
    llm = ChatAnthropic(
        model=os.getenv('ANTHROPIC_RAG_MODEL'), temperature=0
    )
elif os.getenv('MODEL_SRC') == 'OPENAI':
    llm = ChatOpenAI(
        model=os.getenv('OPENAI_RAG_MODEL'), temperature=0
    )

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# RETRIEVAL GRADER
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Data model
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


structured_llm_grader_retrieval = llm.with_structured_output(GradeDocuments)

# Prompt
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", DOC_GRADER_SYSTEM),
        ("human", DOC_GRADER_HUMAN),
    ]
)
retrieval_grader = grade_prompt | structured_llm_grader_retrieval

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# RESPONSE GENERATOR
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Prompt
prompt = ChatPromptTemplate.from_messages(
    [
        ("human", GENERATOR)
    ]
)
# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
# Chain
rag_chain = prompt | llm | StrOutputParser()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# HALLUCINATION GRADER
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Data model
class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )

# LLM with function call
structured_llm_grader_hallucination = llm.with_structured_output(GradeHallucinations)

# Prompt
hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", HALLUCINATION_GRADER_SYSTEM),
        ("human", HALLUCINATION_GRADER_HUMAN),
    ]
)
hallucination_grader = hallucination_prompt | structured_llm_grader_hallucination


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ANSWER GRADER
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Data model
class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""

    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )

# LLM with function call
structured_llm_grader_answer = llm.with_structured_output(GradeAnswer)
# Prompt
answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", ANSWER_GRADER_SYSTEM),
        ("human", ANSWER_GRADER_HUMAN),
    ]
)
answer_grader = answer_prompt | structured_llm_grader_answer

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# QUESTION RE-WRITER
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Prompt
re_write_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", REWRITER_SYSTEM),
        (
            "human", REWRITER_HUMAN
            ,
        ),
    ]
)
question_rewriter = re_write_prompt | llm | StrOutputParser()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DEFINE GRAPH STATE
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
    """

    question: str
    generation: str
    documents: List[str]
    recursion: int
    sender: str

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DEFINE NODES
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def retrieve(state):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """

    print("---RETRIEVE---")
    generation = ""
    recursion = state.get('recursion',0)
    sender = state.get('sender','NA')
    print("STATE_REC:", recursion)
    print("STATE_SEN:", sender)
    if sender == 'NA':
        recursion = 0
    else:
        recursion += 1
    
    question = state["question"]

    # Retrieval
    documents = retriever.invoke(question)
    return {"question": question, "generation": generation, "documents": documents, "recursion":recursion, "sender":"retrieve"}


def generate(state):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """

    print("---GENERATE---")
    generation = ""
    recursion = state.get('recursion',0)
    sender = state.get('sender','NA')
    print("STATE_REC:", recursion)
    print("STATE_SEN:", sender)
    if sender != 'grade_documents':
        recursion += 1
    
    question = state["question"]
    documents = state["documents"]

    # RAG generation
    generation = rag_chain.invoke({"context": documents, "question": question})
    return {"question": question, "generation": generation, "documents": documents, "recursion":recursion, "sender":"generate"}


def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with only filtered relevant documents
    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    generation = ""
    recursion = state.get('recursion',0)

    question = state["question"]
    documents = state["documents"]

    # Score each doc
    filtered_docs = []
    for d in documents:
        score = retrieval_grader.invoke(
            {"question": question, "document": d.page_content}
        )
        grade = score.binary_score
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            continue
    # return {"documents": filtered_docs, "question": question}
    return {"question": question, "generation": generation, "documents": filtered_docs, "recursion":recursion, "sender":"grade_documents"}


def transform_query(state):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """

    print("---TRANSFORM QUERY---")
    generation = ""
    recursion = state.get('recursion',0)

    question = state["question"]
    documents = state["documents"]

    # Re-write question
    better_question = question_rewriter.invoke({"question": question})
    # return {"documents": documents, "question": better_question}
    return {"question": better_question, "generation": generation, "documents": documents, "recursion":recursion, "sender":"transform_query"}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DEFINE EDGE LOGIC
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    print("---ASSESS GRADED DOCUMENTS---")
    recursion = state.get('recursion','0')
    print("STATE_REC:", recursion)
    if past_recursion(recursion):
        return "exceeded_limit"

    state["question"]
    filtered_documents = state["documents"]

    if not filtered_documents:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print(
            "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "transform_query"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE---")
        return "generate"


def grade_generation_v_documents_and_question(state):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """

    print("---CHECK HALLUCINATIONS---")
    recursion = state.get('recursion','0')
    print("STATE_REC:", recursion)
    if past_recursion(recursion):
        return "exceeded_limit"
    
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]

    score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation}
    )
    grade = score.binary_score

    # Check hallucination
    if grade == "yes":
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        # Check question-answering
        print("---GRADE GENERATION vs QUESTION---")
        score = answer_grader.invoke({"question": question, "generation": generation})
        grade = score.binary_score
        if grade == "yes":
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:
        pprint("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"
    
def past_recursion(recursion):
    print("RECURSION:", recursion, 'vs', int(os.getenv('RAG_RECURSION_LIMIT')))
    if recursion > int(os.getenv('RAG_RECURSION_LIMIT')):
        pprint("---RECURSION LIMIT REACHED, EXITING RAG---")
        return True
    else:
        return False
    
def limit_returner(state):
    generation = 'Exceeded recursion limit, could not complete the task as requested.'
    return {"generation": generation, "sender":"limit_returner"}

    
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DEFINE GRAPH
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("retrieve", retrieve)  # retrieve
workflow.add_node("grade_documents", grade_documents)  # grade documents
workflow.add_node("generate", generate)  # generatae
workflow.add_node("transform_query", transform_query)  # transform_query
workflow.add_node("limit_node", limit_returner)

# Build graph
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
        "exceeded_limit": "limit_node"
    },
)
workflow.add_edge("transform_query", "retrieve")
workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_question,
    {
        "not supported": "generate",
        "useful": END,
        "not useful": "transform_query",
        "exceeded_limit": "limit_node"
    },
)

workflow.add_edge("limit_node", END)

# Compile
rag_graph = workflow.compile()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# GRAPH VIEWER
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# try:
#     # Get the PNG image as bytes
#     img_data = rag_graph.get_graph().draw_mermaid_png()  # Image data in bytes

#     # Use BytesIO to open the image directly from bytes
#     img = Image.open(io.BytesIO(img_data))
#     img.show()  # This opens the image with the default viewer without saving it to disk
#     img.save('./misc/TOOLRAG_RAGGraph_Img.png')
# except Exception as e:
#     print(f"Error displaying image: {e}")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# RUN PROCESS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# inputs = {"question": "Tell me how to avoid my cookies being open to client-side scripts?"}
# inputs = {"question": "What is CWE-288??"}
# for output in rag_graph.stream(inputs):
#     for key, value in output.items():
#         # Node
#         pprint(f"Node '{key}':")
#         # Optional: print full state at each node
#         pprint(value, indent=2, width=80, depth=None)
#     pprint("\n---\n")

# # Final generation
# pprint(key)
# pprint(value["generation"])