import getpass
import os
from dotenv import load_dotenv
from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from PIL import Image
import io

# Model Specific
from langchain_anthropic import ChatAnthropic

# Custom Files
from sasts import *
from prompts import *
from prompters import *

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

# tools = [run_flawfinder, run_cppcheck, run_appinspector, run_semgrep]
tools = [run_flawfinder]
tool_node = ToolNode(tools)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# MODELS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Supervisor Model: claude-3-sonnet-20240229
# Analysis model: claude-3-5-sonnet-20241022 OR claude-3-opus-20240229
# Tool Model: claude-3-haiku-20240307
# Summarize Model: claude-3-haiku-20240307 OR claude-3-sonnet-20240229
# RAG Model: ?

sast_model = ChatAnthropic(
    model="claude-3-haiku-20240307", temperature=0
).bind_tools(tools)

summarize_model = ChatAnthropic(
    model="claude-3-sonnet-20240229", temperature=0
)

# supervisor_model = ChatAnthropic(
#     model="claude-3-haiku-20240307", temperature=0
# )

analysis_model = ChatAnthropic(
    model="claude-3-5-sonnet-20241022", temperature=0
)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ReAct AGENTS LANGGRAPH
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langgraph.graph import END, StateGraph, START

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
                " If you or any of the other assistants have the final answer or deliverable,"
                " prefix your response with FINAL ANSWER so the team knows to stop."
                " You have access to the following tools: {tool_names}.\n{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))

    return prompt | llm
    
sast_agent = create_agent(
    sast_model,
    tools,
    system_message="You should run all relevent static analysis tools to provide outputs for the Summarizer to use.",
)

summarize_agent = create_agent(
    summarize_model,
    [],
    system_message="You should provide accurate summarizations of information for all other models to use.",
)

# supervisor_agent = create_agent(
#     supervisor_model,
#     [],
#     system_message="???",
# )

analyze_agent = create_agent(
    analysis_model,
    [],
    system_message="You should use the provided information to detect all potential vulnerabilties in a code sample. You may request additional information. You should avoid false positives and false negatives."
)

import operator
from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
import functools
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode
from typing import Literal

# !!!!!!!!!!!!! DEFINE STATE !!!!!!!!!!!!!

# This defines the object that is passed between each node
# in the graph. We will create different nodes for each agent and tool
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str

class SubAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str

# !!!!!!!!!!!!! DEFINE AGENT NODES !!!!!!!!!!!!!

# Func to aggregate tool responses
def aggregate_responses(responses):
    """Aggregate responses from tools into a single dictionary."""
    aggregated = {}
    for response in responses:
        for key, value in response.items():
            if key in aggregated:
                aggregated[key].append(value)
            else:
                aggregated[key] = [value]
    # Format the aggregated responses
    for key in aggregated:
        aggregated[key] = ', '.join(aggregated[key])
    return aggregated

# Helper function to create a node for a given agent
def agent_node(state, agent, name):
    print(name)
    # print(state)
    # print('~'*100)

    result = agent.invoke(state)
    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        # print('TOOLMSG')
        # print(result)
        # print('~'*100)
        pass
    else:
        # print('PRE RM')
        # print(result)
        # print('+'*100)
        # print('DUMPED')
        # print(result.model_dump())
        # print('+'*100)
        # result = AIMessage(**result.model_dump(exclude={"type", "name"}), name=name)
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
        # print('POST RM')
        # print(result)
        # print('+'*100)
    return {
        "messages": [result],
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }

sast_node = functools.partial(agent_node, agent=sast_agent, name="Sast_runner")
summarize_node = functools.partial(agent_node, agent=summarize_agent, name="Summarizer")
# supervisor_node = functools.partial(agent_node, agent=supervisor_agent, name="Supervisor")
analyze_node = functools.partial(agent_node, agent=analyze_agent, name="Analyzer")

# !!!!!!!!!!!!! DEFINE EDGE LOGIC !!!!!!!!!!!!!

# Either agent can decide to end
def router(state):
    # This is the router
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        # The previous agent is invoking a tool
        return "call_tool"
    if "FINAL ANSWER" in last_message.content and last_message.name == 'Summarizer':
        # Any agent decided the work is done
        return END
    return "continue"

# !!!!!!!!!!!!! DEFINE THE GRAPH !!!!!!!!!!!!!

# Subgraph
sast_workflow = StateGraph(SubAgentState)
sast_workflow.add_node("Sast_runner", sast_node)
sast_workflow.add_node("call_tool", tool_node)
sast_workflow.add_edge(START,"Sast_runner")
sast_workflow.add_conditional_edges(
    "Sast_runner",
    router,
    {"call_tool": "call_tool"},
)
sast_workflow.add_conditional_edges(
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

sast_workflow_node = sast_workflow.compile()

workflow = StateGraph(AgentState)

workflow.add_node("Summarizer", summarize_node)
# workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Analyzer", analyze_node)
workflow.add_node("Sast_graph", sast_workflow_node)

workflow.add_edge(START, "Sast_graph")

workflow.add_edge("Sast_graph", "Summarizer")

workflow.add_conditional_edges(
    "Summarizer",
    router,
    {"continue": "Analyzer", END: END},
)
workflow.add_conditional_edges(
    "Analyzer",
    router,
    {"continue": "Summarizer"},
)


graph = workflow.compile()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ReAct AGENTS GRAPH VIEWER
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# try:
#     # Get the PNG image as bytes
#     img_data = graph.get_graph().draw_mermaid_png()  # Image data in bytes

#     # Use BytesIO to open the image directly from bytes
#     img = Image.open(io.BytesIO(img_data))
#     img.show()  # This opens the image with the default viewer without saving it to disk
# except Exception as e:
#     print(f"Error displaying image: {e}")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# PROMPTS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

samples, convos = form_prompts('BRYSON',SAST_PROMPT, 1)
convos = truncate_tokens_from_messages(convos, "claude-3-haiku-20240307", 2048)
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

for msgs in convos:
    events = graph.stream(
        {
            "messages": msgs
        },
        # Maximum number of steps to take in the graph
        {"recursion_limit": 150},
    )
    for s in events:
        print(s)
        print("----")