from langgraph import LangGraph, ToolNode, Node
from langchain_core.tools import tool

# Define the tool functions
@tool
def tool1_function(input_data):
    return f"Output from Tool1 processing '{input_data}'"

@tool
def tool2_function(input_data):
    return f"Output from Tool2 processing '{input_data}'"

# Define a summarization function for modelB
def modelB_summarize(tool_outputs):
    summary = " | ".join(tool_outputs)
    return f"Summary of outputs: {summary}"

# Create ToolNodes for each tool
tool1 = ToolNode(name="Tool1", function=tool1_function)
tool2 = ToolNode(name="Tool2", function=tool2_function)

# Create a node for modelB
nodeB = Node(name="modelB", function=modelB_summarize)

# Create a LangGraph and add the ToolNodes and model node
graph = LangGraph()
graph.add_node(tool1)
graph.add_node(tool2)
graph.add_node(nodeB)

# Define edges to connect ToolNodes to modelB
graph.add_edge(from_node=tool1, to_node=nodeB)
graph.add_edge(from_node=tool2, to_node=nodeB)

# Function to run the LangGraph
def run_langgraph(input_data):
    # Collect outputs from ToolNodes
    tool_outputs = [tool.run(input_data) for tool in graph.get_tool_nodes()]
    
    # Pass the outputs to modelB
    summary = nodeB.run(tool_outputs)
    return summary

# Example input data
input_data = "Example input data for processing."
output_summary = run_langgraph(input_data)
print("Summary from modelB:", output_summary)
