import getpass
import os
from dotenv import load_dotenv
from typing import Literal
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from PIL import Image
import io

# Model Specific
from langchain_anthropic import ChatAnthropic

# Custom Files
import sasts

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# LOGIN
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
load_dotenv()

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("ANTHROPIC_API_KEY")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DEFINE TOOLS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@tool
def run_flawfinder(code_sample: str, file_suffix: str) -> str:
    """Call to run the Flawfinder static analysis tool."""
    return sasts.go_flawfinder(code_sample, file_suffix)

tools = [run_flawfinder]
tool_node = ToolNode(tools)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DEMOS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

test_code_snip = (
    "void calculateDiscountedPrice(char *userInput, int itemPrice, float discountRate) {\n"
    "    char buffer[10];\n"
    "    int discountedPrice;\n"
    "    float discountAmount;\n"
    "    if (isLoggedIn) {\n"
    "        strcpy(buffer, userInput);\n"
    "        discountAmount = (itemPrice * discountRate) / 100;\n"
    "        discountedPrice = itemPrice - (int)discountAmount;\n"
    "        sprintf(buffer, \"Discounted Price: %d\", discountedPrice);\n"
    "        printf(\"%s\\n\", buffer);\n"
    "    } else {\n"
    "        printf(\"User is not logged in.\\n\");\n"
    "    }\n"
"}\n"
)
test_code_ext = ".cpp"

# message_with_single_tool_call = AIMessage(
#     content="",
#     tool_calls=[
#         {
#             "name": "run_flawfinder",
#             "args": {'code_sample': test_code_snip, 'file_suffix':test_code_ext},
#             "id": "tool_call_id",
#             "type": "tool_call",
#         }
#     ],
# )

# tool_node.invoke({"messages": [message_with_single_tool_call]})

# # message_with_multiple_tool_calls = AIMessage(
# #     content="",
# #     tool_calls=[
# #         {
# #             "name": "get_coolest_cities",
# #             "args": {},
# #             "id": "tool_call_id_1",
# #             "type": "tool_call",
# #         },
# #         {
# #             "name": "get_weather",
# #             "args": {"location": "sf"},
# #             "id": "tool_call_id_2",
# #             "type": "tool_call",
# #         },
# #     ],
# # )

# # tool_node.invoke({"messages": [message_with_multiple_tool_calls]})

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TEST WITH MODEL
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

model_with_tools = ChatAnthropic(
    model="claude-3-haiku-20240307", temperature=0
).bind_tools(tools)

# mwt_tool_calls = model_with_tools.invoke(f"Is this {test_code_ext} code vulnerable?\n\n{test_code_snip}").tool_calls
# print(mwt_tool_calls)

# mwt_result = tool_node.invoke({"messages": [model_with_tools.invoke(f"Is this {test_code_ext} code vulnerable?\n\n{test_code_snip}")]})
# print(mwt_result)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ReAct Agent
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

def call_model(state: MessagesState):
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

workflow = StateGraph(MessagesState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

app = workflow.compile()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Display ReAct Agent Graph
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# try:
#     # Get the PNG image as bytes
#     img_data = app.get_graph().draw_mermaid_png()  # Image data in bytes

#     # Use BytesIO to open the image directly from bytes
#     img = Image.open(io.BytesIO(img_data))
#     img.show()  # This opens the image with the default viewer without saving it to disk
# except Exception as e:
#     print(f"Error displaying image: {e}")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Sample Calls to ReAct Agent
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# example with a single tool call
for chunk in app.stream(
    {"messages": [("human", f"Is this {test_code_ext} code vulnerable?\n\n{test_code_snip}")]}, stream_mode="values"
):
    chunk["messages"][-1].pretty_print()

# # example with a multiple tool calls in succession

# for chunk in app.stream(
#     {"messages": [("human", "what's the weather in the coolest cities?")]},
#     stream_mode="values",
# ):
#     chunk["messages"][-1].pretty_print()


