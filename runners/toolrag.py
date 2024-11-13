import getpass
import os
import io
import operator
import functools
from dotenv import load_dotenv
from typing import Literal, Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage, ToolMessage, SystemMessage, ChatMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from PIL import Image
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Model Specific
from langchain_anthropic import ChatAnthropic

# Custom Files
from sasts import *
from prompts import *
from prompters import *
from rag import rag_graph

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# LOGIN
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
load_dotenv()

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")

_set_env("ANTHROPIC_API_KEY")
_set_env("OPENAI_API_KEY")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DEFINE TOOLS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@tool
def dummy_tool() -> str:
    """This tool is NEVER to be used. It only exists to avoid errors."""
    return "Dummy tool call"

@tool
def run_flawfinder(code_sample: str, file_suffix: str) -> str:
    """Call to run the Flawfinder static analysis tool."""
    return go_flawfinder(code_sample, file_suffix)

@tool
def run_cppcheck(code_sample: str, file_suffix: str) -> str:
    """Call to run the CppCheck static analysis tool."""
    return go_cppcheck(code_sample, file_suffix)

@tool
def run_appinspector(code_sample: str, file_suffix: str) -> str:
    """Call to run the AppInspector static analysis tool."""
    return go_appinspector(code_sample, file_suffix)

@tool
def run_semgrep(code_sample: str, file_suffix: str) -> str:
    """Call to run the Semgrep static analysis tool."""
    return go_semgrep(code_sample, file_suffix)

sast_tools = [run_flawfinder, run_cppcheck, run_appinspector, run_semgrep]
fake_tools = [dummy_tool]
tool_node = ToolNode(sast_tools+fake_tools)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# MODELS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Analysis model: claude-3-5-sonnet-20241022 OR claude-3-opus-20240229
# SAST Model: claude-3-haiku-20240307
# Summarize Model: claude-3-haiku-20240307 OR claude-3-sonnet-20240229
# RAG Model: claude-3-haiku-20240307

if os.getenv('MODEL_SRC'):
    sast_model = ChatAnthropic(
        model=os.getenv('ANTHROPIC_SAST_MODEL'), temperature=0
    )

    summarize_model = ChatAnthropic(
        model=os.getenv('ANTHROPIC_SUMMARIZE_MODEL'), temperature=0
    )

    analysis_model = ChatAnthropic(
        model=os.getenv('ANTHROPIC_ANALYSIS_MODEL'), temperature=0
    )

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ReAct AGENTS LANGGRAPH
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def create_agent(llm, tools, system_message: str):
    """Create an agent."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK, another assistant with different tools "
                " will help where you left off. Execute what you can to make progress."
                " You are not allowed to return an empty response under any circumstance, instead state DONE."
                " You have access to the following tools: {tool_names}.\n{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))

    return prompt | llm.bind_tools(tools)
    
sast_agent = create_agent(
    sast_model,
    sast_tools,
    system_message="You should run all relevent static analysis tools to provide outputs for the Summarizer to use. If you are done running tools, you must state 'No more applicable tools.'",
)

summarize_agent = create_agent(
    summarize_model,
    fake_tools,
    system_message="You should provide accurate summarizations of previously generated information for all other models to use.",
)

analyze_agent = create_agent(
    analysis_model,
    fake_tools,
    system_message="You should use the provided information to detect all potential vulnerabilties in the originally presented code sample. You may request additional information. You should avoid false positives and false negatives."
)

# !!!!!!!!!!!!! DEFINE STATE !!!!!!!!!!!!!

# This defines the object that is passed between each node
# in the graph. We will create different nodes for each agent and tool
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str
    target: str

# !!!!!!!!!!!!! DEFINE AGENT NODES !!!!!!!!!!!!!

# Function to run RAG subgraph
def call_rag(state):
    rag_input = {'question': state['messages'][-1].dict().get('content', '')}
    rag_output = rag_graph.invoke(rag_input)
    print(rag_output)
    return {
        'messages': [AIMessage(rag_output['generation'], name='Rag_subgraph')],
        'sender': 'Rag_subgraph',
        'target': 'Prompter_node'
    }

# Fake Human Node to provide checkpoint prompts
def human_feedback(state):
    results = state['messages'][-1].dict().get('content', '')
    if state['sender'] == 'Sast_runner':
        prompt = ("Please summarize all of the static analysis results from all of the previous tool runs."
                  " Indicate which tools you are summarizing in your response."
        )
        target = 'Summarizer'
    elif state['sender'] == 'Analyzer':
        last_msg = state['messages'][-1].dict().get('content', '')
        if 'QNA:' in last_msg:
            loc = last_msg.find('QNA:')
            prompt = last_msg[loc:]
            target = 'Rag_subgraph'
        else:
            prompt = ("Prepend your response with FINAL ANSWER. Follow this with VULNERABLE or SAFE depending on the results."
                    " Immediately after, include a CONFIDENCE SCORE, with a score describing your certainty regarding"
                    " your analysis on a scale from 0 to 10."
                    " Please summarize the following results:"
                    f"\n{results}"
            )
            target = 'Summarizer'
    elif state['sender'] == 'Summarizer':
        prompt = ("Please utilize the output of the summary to inform your analysis of the original code sample."
                  " Evaluate it for any vulnerabilities you can find while avoiding false positives."
                  " Intensively review all detections, reasoning through to ensure they are accurate."
                  " If no true positive vulnerabilities are found respond NONE."
                  " You have access to a peer RAG agent. If you would like more basic information on a vulnerability,"
                  " then at the end of your response, respond with 'QNA:', then your list of questions. Your questions"
                  " should be at the very end of your message. Keep your questions as simple as possible, as you are"
                  " querying the Common Weakness Enumeration database. An example request would be to provide a" 
                  " description or example of a specific type of vulnerability."
        )
        target = 'Analyzer'
    elif state['sender'] == 'Rag_subgraph':
        prompt = f'The answers to your questions are as follows:\n{results}'
        target = 'Analyzer'
    msg = HumanMessage(prompt, name='Prompter_node')
    return {
        "messages": [msg],
        "sender": 'Prompter_node',
        "target": target
    }

# Helper function to create a node for a given agent
def agent_node(state, agent, name):
    result = agent.invoke(state)
    result = result.dict(exclude={"type", "name"})
    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        pass
    # elif len(result['content']) > 0:
    else:
        # result = msg_type(**result, name=name)
        result = AIMessage(**result, name=name)
        # pass
    return {
        "messages": [result],
        "sender": name,
        "target": "Prompter_node"
    }

sast_node = functools.partial(agent_node, agent=sast_agent, name="Sast_runner")
summarize_node = functools.partial(agent_node, agent=summarize_agent, name="Summarizer")
analyze_node = functools.partial(agent_node, agent=analyze_agent, name="Analyzer")

# !!!!!!!!!!!!! DEFINE EDGE LOGIC !!!!!!!!!!!!!

# Either agent can decide to end
def router(state):
    # This is the router
    messages = state["messages"]
    last_message = messages[-1].dict()

    print('IN ROUTER FOR:', last_message.get('name', ''))
    # print(state)

    if last_message.get('tool_calls',0):
        # The previous agent is invoking a tool
        return "call_tool"
    
    if "FINAL ANSWER" in last_message.get('content','') and last_message.get('name','') == 'Summarizer':
        # End of workflow
        return END
    
    if state['sender'] == 'Prompter_node':
        if state['target'] == 'Analyzer':
            return "goAnalyze"
        elif state['target'] == 'Rag_subgraph':
            return "goRag"
        else:
            return "goSummarize"

    return "continue"

# !!!!!!!!!!!!! DEFINE THE GRAPH !!!!!!!!!!!!!

workflow = StateGraph(AgentState)

workflow.add_node("Rag_subgraph", call_rag)
workflow.add_node("Prompter_node", human_feedback)
workflow.add_node("Sast_runner", sast_node)
workflow.add_node("Summarizer", summarize_node)
workflow.add_node("Analyzer", analyze_node)
workflow.add_node("call_tool", tool_node)


workflow.add_conditional_edges(
    "Sast_runner",
    router,
    {"continue": "Prompter_node", "call_tool": "call_tool"},
)
workflow.add_conditional_edges(
    "Summarizer",
    router,
    {"continue": "Prompter_node", END: END},
)
workflow.add_conditional_edges(
    "Analyzer",
    router,
    {"continue": "Prompter_node"},
)
workflow.add_conditional_edges(
    "Rag_subgraph",
    router,
    {"continue":"Prompter_node"}
)
workflow.add_conditional_edges(
    "Prompter_node",
    router,
    {"goSummarize": "Summarizer", "goAnalyze": "Analyzer", "goRag":"Rag_subgraph"},
)

workflow.add_conditional_edges(
    "call_tool",
    # Each agent node updates the 'sender' field
    # the tool calling node does not, meaning
    # this edge will route back to the original agent
    # who invoked the tool
    lambda x: x["sender"],
    {
        "Sast_runner": "Sast_runner",
    },
)
workflow.add_edge(START, "Sast_runner")
graph = workflow.compile()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ReAct AGENTS GRAPH VIEWER
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# try:
#     # Get the PNG image as bytes
#     img_data = graph.get_graph(xray=True).draw_mermaid_png()  # Image data in bytes

#     # Use BytesIO to open the image directly from bytes
#     img = Image.open(io.BytesIO(img_data))
#     img.show()  # This opens the image with the default viewer without saving it to disk
#     img.save('./misc/TOOLRAG_RUNGraph_Img.png')
# except Exception as e:
#     print(f"Error displaying image: {e}")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# PROMPTS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

samples, convos = form_prompts('PRIMEVUL',SAST_PROMPT, 1)

# print(convos)

# One-Off Sample
# test_code_snip = (
#     "void calculateDiscountedPrice(char *userInput, int itemPrice, float discountRate) {\n"
#     "    char buffer[10];\n"
#     "    int discountedPrice;\n"
#     "    float discountAmount;\n"
#     "    if (isLoggedIn) {\n"
#     "        strcpy(buffer, userInput);\n"
#     "        discountAmount = (itemPrice * discountRate) / 100;\n"
#     "        discountedPrice = itemPrice - (int)discountAmount;\n"
#     "        sprintf(buffer, \"Discounted Price: %d\", discountedPrice);\n"
#     "        printf(\"%s\\n\", buffer);\n"
#     "    } else {\n"
#     "        printf(\"User is not logged in.\\n\");\n"
#     "    }\n"
# "}\n"
# )
# test_code_ext = ".cpp"
# msgs = [("human", f"Is this {test_code_ext} code vulnerable?\n\n{test_code_snip}")]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CALL ReAct AGENT
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def extract_vulnerability_info(text):
    # Regex patterns to match "VULNERABLE" status and the confidence score
    status_pattern = r"FINAL ANSWER:\s*(\w+)"
    confidence_pattern = r"CONFIDENCE SCORE:\s*(\d+)"

    # Find matches
    status_match = re.search(status_pattern, text)
    confidence_match = re.search(confidence_pattern, text)

    # Extract values if found
    status = 1 if status_match else 0
    confidence_score = int(confidence_match.group(1)) if confidence_match else None

    return status, confidence_score

for i in range(0,len(convos)):
    msgs = convos[i]
    events = graph.stream(
        {
            "messages": msgs
        },
        # Maximum number of steps to take in the graph
        {"recursion_limit": 150},
        stream_mode='debug'
    )
    
    directory_path = os.getenv('OUTPUT_PTH')
    num_items = len(os.listdir(directory_path+'/full'))
    f =  open(f"{directory_path}/full/run_{num_items}_full.txt","a+", encoding="utf-8", errors="replace")
    
    second_to_last_event = None
    last_event = None
    
    for s in events:
        print(s)
        print("----")
        f.write(str(s))
        f.write("\n----\n")

        second_to_last_event = last_event  # Update second-to-last to the previous last
        last_event = s 
    f.close()

    with open(f"{directory_path}/parsed/run_{num_items}_parsed.txt", "a+", encoding="utf-8", errors="replace") as f2:
        isFirst = True
        for msg in second_to_last_event['payload']['input']['messages']:            
            msg_dict = msg.dict()

            if msg_dict['response_metadata'].get('stop_reason','') != 'tool_use':
                if isFirst:
                    f2.write("-"*50 + "\nINPUT\n" + "-"*50 + "\n")
                    isFirst = False
                else:
                    f2.write("\n" + "-"*50 + f"\n{msg_dict.get('name', 'NAME NOT FOUND')}\n" + "-"*50 + "\n")
                
                f2.write(msg_dict.get('content','CONTENT NOT FOUND'))
                f2.write("\n")
        
        f2.write("\n"+"-"*50 + "\nFINAL SUMMARY OUTPUT\n" + "-"*50 + "\n")
        final_output = last_event['payload']['result'][0][1][0].dict().get('content','')
        f2.write(final_output)

    with open(f"{directory_path}/verdicts.csv", "a+", encoding="utf-8", errors="replace") as f3:
        # run, source, idx, true_vuln, predicted_vuln, predicted_confidence
        status, confidence = extract_vulnerability_info(final_output)
        line = [num_items, samples[i]['source'], samples[i]['idx'], samples[i]['vuln'], status, confidence]
        f3.write(", ".join(line))