import getpass
import os
from dotenv import load_dotenv

load_dotenv()

def _set_if_undefined(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")

_set_if_undefined("ANTHROPIC_API_KEY")

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage, ChatMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from typing_extensions import TypedDict

# Define the dummy tool
@tool
def dummy_tool() -> str:
    """Tool that just returns output 'HELLO WORLD!'"""
    return "HELLO WORLD!"

# Define the models for the agents
agent_1_model = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)
agent_2_model = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0)

import operator
from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
import functools
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode
from typing import Literal
# Define the state schema
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str

# Create agent 1 with tool access
def create_agent_with_tool(model, tools):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an assistant with access to specific tools that provide output messages to a summarizer agent."),
        MessagesPlaceholder(variable_name="messages"),
    ])
    return prompt | model.bind_tools(tools)

# Create agent 2 without tool access
def create_agent_without_tool(model):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an assistant who summarizes messages. Include the word FINAL at the end of your summary."),
        MessagesPlaceholder(variable_name="messages"),
    ])
    return prompt | model  # No tool binding

# Initialize agents
agent_1 = create_agent_with_tool(agent_1_model, [dummy_tool])
agent_2 = create_agent_without_tool(agent_2_model)

# Define the graph
state_graph = StateGraph(AgentState)  # Set START as input and END as output

# Control number of previous messages used
def filter_messages(messages: list, amt:int):
    # This is very simple helper function which only ever uses the last message
    print('+'*100,'\n', messages[amt:], '+'*100,'\n')
    return messages[amt:]

# Either agent can decide to end
def router(state):
    # This is the router
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        # The previous agent is invoking a tool
        return "call_tool"
    if "FINAL" in last_message.content:
        # Any agent decided the work is done
        return END
    return "continue"

# Agent 1 node with tool use
def agent_1_node(state):
    # Agent 1 calls the dummy tool
    print('A1 STATE:')
    print(state)
    print('~'*100)
    result = agent_1.invoke(filter_messages(state['messages'], 0))
    result = AIMessage(**result.dict(exclude={"type", "name"}), name='a1', role='helper')
    print('A1 RESULT:', result)
    return {
        "messages": [result],
        "sender": 'a1',
    }

# Agent 2 node without tool use
def agent_2_node(state):
    # Remove any `tool_use` data from the messages list before Agent 2 processes it
    # state["messages"] = [clean_tool_content(message) for message in state["messages"]]
    print('A2 STATE:')
    print(state)
    print('~'*100)
    result = agent_2.invoke(filter_messages(state['messages'], -1))
    result = ChatMessage(**result.dict(exclude={"type", "name"}), name='a2', role='summarizer')
    print('A2 RESULT:', result)
    return {
        "messages": [result],
        "sender": 'a2',
    }

# Add Nodes
tool_node = ToolNode([dummy_tool])
state_graph.add_node("a1", agent_1_node)
state_graph.add_node("a2", agent_2_node)
state_graph.add_node("call_tool", tool_node)

# Setup graph edges
state_graph.add_conditional_edges(
    "a1",
    router,
    {"continue": "a2", "call_tool": "call_tool"},
)
state_graph.add_conditional_edges(
    "a2",
    router,
    {"continue": "a1", END:END},
)

state_graph.add_edge(START, "a1")

state_graph.add_conditional_edges(
    "call_tool",
    # Each agent node updates the 'sender' field
    # the tool calling node does not, meaning
    # this edge will route back to the original agent
    # who invoked the tool
    lambda x: x["sender"],
    {
        "a1": "a1",
    },
)

graph = state_graph.compile()

# Initialize state and run the graph
events = graph.stream(
    {
        "messages": [HumanMessage(content="Call your tool and provide the tool output to your peers as a block of text.")]
    },
    # Maximum number of steps to take in the graph
    {"recursion_limit": 150},
)
for s in events:
    print(s)
    print("----")
