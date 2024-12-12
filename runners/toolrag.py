import getpass
import os
import io
import ast
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
from langchain_openai import ChatOpenAI

# Custom Files
from sasts import *
from prompts import *
from prompters import *
from rag import rag_graph
from get_results import getResults

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# LOGIN
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
load_dotenv()

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")

_set_env("ANTHROPIC_API_KEY")
_set_env("OPENAI_API_KEY")

VERBOSE = int(os.getenv('VERBOSE'))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DEFINE TOOLS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@tool
def dummy_tool() -> str:
    """THIS FUNCTION MAY NEVER, EVER BE CALLED UNDER ANY CIRCUMSTANCES."""
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

# Start SEMGREP
start_semgrep_container()

sast_tools = [run_flawfinder, run_cppcheck, run_appinspector, run_semgrep]
fake_tools = [dummy_tool]
tool_node = ToolNode(sast_tools+fake_tools)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# MODELS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if os.getenv('MAIN_MODEL_SRC') == 'ANTHROPIC':
    sast_model = ChatAnthropic(
        model=os.getenv('ANTHROPIC_SAST_MODEL'), temperature=0
    )

    summarize_model = ChatAnthropic(
        model=os.getenv('ANTHROPIC_SUMMARIZE_MODEL'), temperature=0
    )

    analysis_model = ChatAnthropic(
        model=os.getenv('ANTHROPIC_ANALYSIS_MODEL'), temperature=0
    )
elif os.getenv('MAIN_MODEL_SRC') == 'OPENAI':
    sast_model = ChatOpenAI(
        model=os.getenv('OPENAI_SAST_MODEL'), temperature=0
    )

    summarize_model = ChatOpenAI(
        model=os.getenv('OPENAI_SUMMARIZE_MODEL'), temperature=0
    )

    analysis_model = ChatOpenAI(
        model=os.getenv('OPENAI_ANALYSIS_MODEL'), temperature=0
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
                AGENT_PROMPT,
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
    system_message=SAST_SYSTEM_PROMPT
)

summarize_agent = create_agent(
    summarize_model,
    fake_tools,
    system_message=SUMMARIZE_SYSTEM_PROMPT
)

analyze_agent = create_agent(
    analysis_model,
    fake_tools,
    system_message=ANALYZE_SYSTEM_PROMPT
)

# !!!!!!!!!!!!! DEFINE STATE !!!!!!!!!!!!!

# This defines the object that is passed between each node
# in the graph. We will create different nodes for each agent and tool
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str
    target: str
    rag_calls: int

# !!!!!!!!!!!!! DEFINE AGENT NODES !!!!!!!!!!!!!

# Function to run RAG subgraph
def call_rag(state):
    rag_input = {'question': state['messages'][-1].dict().get('content', '')}
    rag_output = rag_graph.invoke(rag_input)
    if VERBOSE:
        print(rag_output)
    return {
        'messages': [AIMessage(rag_output['generation'], name='Rag_subgraph')],
        'sender': 'Rag_subgraph',
        'target': 'Prompter_node',
        'rag_calls': state.get('rag_calls',int(os.getenv('RAG_CALL_LIMIT')))-1
    }

# Fake Human Node to provide checkpoint prompts
def human_feedback(state):
    results = state['messages'][-1].dict().get('content', '')
    if state['sender'] == 'Sast_runner':
        prompt = HUMAN_SAST_SUMMARIZER
        target = 'Summarizer'
    elif state['sender'] == 'Analyzer':
        last_msg = state['messages'][-1].dict().get('content', '')
        if 'QNA:' in last_msg:
            loc = last_msg.find('QNA:')
            prompt = last_msg[loc:]
            target = 'Rag_subgraph'
        else:
            prompt = HUMAN_ANALYZER_SUMMARIZER.format(results=results)
            target = 'Summarizer'
    elif state['sender'] == 'Summarizer':
        prompt = HUMAN_SUMMARIZER_ANALYZER
        target = 'Analyzer'
    elif state['sender'] == 'Rag_subgraph':
        if state.get('rag_calls',-1) <= 0:
            prompt = HUMAN_RAGLIMIT_ANALYZER.format(results=results)
        else:
            prompt = HUMAN_RAG_ANALYZER.format(results=results)
        target = 'Analyzer'
    msg = HumanMessage(prompt, name='Prompter_node')
    return {
        "messages": [msg],
        "sender": 'Prompter_node',
        "target": target,
        'rag_calls': state.get('rag_calls',int(os.getenv('RAG_CALL_LIMIT')))
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
        "target": "Prompter_node",
        'rag_calls': state.get('rag_calls',int(os.getenv('RAG_CALL_LIMIT')))
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

    if VERBOSE:
        print('IN ROUTER FOR:', last_message.get('name', ''))

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

samples, convos = form_prompts(
    src=os.getenv('DATA_SRC').upper(),
    prompt=START_PROMPT,
    limit=int(os.getenv('SAMPLE_LIMIT')),
    start_idx=int(os.getenv('START_IDX')),
    cherrypick=ast.literal_eval(os.getenv('CHERRYPICK')),
    cherryskip=ast.literal_eval(os.getenv('CHERRYSKIP'))
)

# print(samples)
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
    status = 1 if 'VULN' in status_match.group(1).upper() else 0
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
    # Check if the directory exists
    if not os.path.exists(directory_path+'/full'):
        os.makedirs(directory_path+'/full')
    if not os.path.exists(directory_path+'/parsed'):
        os.makedirs(directory_path+'/parsed')

    num_items = len(os.listdir(directory_path+'/full'))
    f =  open(f"{directory_path}/full/run_{num_items}_full.txt","a+", encoding="utf-8", errors="replace")
    
    second_to_last_event = None
    last_event = None
    
    for s in events:
        if VERBOSE:
            print(s)
        else:
            print(f"{s.get('step')}: {s.get('payload').get('name')}")
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
        # Move cursor to start and check if header is needed
        f3.seek(0)
        if sum(1 for line in f3) == 0:  # If no lines, write header
            header = "run,source,idx,true_vuln,predicted_vuln,predicted_confidence,cwe\n"
            f3.write(header)
        
        # Prepare the line of data to write
        status, confidence = extract_vulnerability_info(final_output)
        line = [
            num_items,
            samples[i]['source'],
            samples[i]['idx'],
            samples[i]['vuln'],
            status,
            confidence,
            json.dumps(samples[i]['cwe'])
        ]
            
        formatted_line = []
        for x in line:
            tmp = str(x).replace('"', "'")
            if '[' in tmp:
                tmp = '"' + tmp + '"'
            formatted_line.append(tmp)
        
        # Write data line to the file
        f3.write(",".join(formatted_line) + "\n")

stop_semgrep_container()
getResults()