from langgraph.graph import StateGraph, END
from app.graph.state import AgentState

from app.graph.nodes.detect_intent import detect_intent
from app.graph.nodes.service_match import match_service
from app.graph.nodes.validate_signal import validate_signal
from app.graph.nodes.identity import resolve_identity

def route_intent(state: AgentState):
    if state.get("is_buying_signal"):
        return "match_service"
    return END

def route_service(state: AgentState):
    if state.get("service_match"):
        return "validate_signal"
    return END

workflow = StateGraph(AgentState)

workflow.add_node("detect_intent", detect_intent)
workflow.add_node("match_service", match_service)
workflow.add_node("validate_signal", validate_signal)
workflow.add_node("resolve_identity", resolve_identity)

workflow.set_entry_point("detect_intent")

workflow.add_conditional_edges("detect_intent", route_intent)
workflow.add_conditional_edges("match_service", route_service)
workflow.add_edge("validate_signal", "resolve_identity")
workflow.add_edge("resolve_identity", END)

app_graph = workflow.compile()
