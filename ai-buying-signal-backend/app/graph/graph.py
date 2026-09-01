from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes.extraction import extract_all

workflow = StateGraph(AgentState)

workflow.add_node("extract_all", extract_all)
workflow.set_entry_point("extract_all")
workflow.add_edge("extract_all", END)

app_graph = workflow.compile()
