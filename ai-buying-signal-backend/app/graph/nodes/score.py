import logging
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

async def score_node(state: AgentState) -> AgentState:
    """
    Final scoring based on extracted LLM fields.
    """
    if not state.get("is_qualified", True):
        state["intent_score"] = 0
        return state
        
    base_score = 50 # Base score for making it past classifier
    
    # Boost based on LLM's buying stage
    stage = state.get("buying_stage", "").lower()
    if "ready" in stage: base_score += 30
    elif "evaluating" in stage: base_score += 20
    elif "researching" in stage: base_score += 10
    
    # Boost if clear service fit is identified
    if state.get("service_fit") and state.get("service_fit") != "Unknown":
        base_score += 20
        
    state["intent_score"] = min(100, base_score)
    logger.info(f"Node [Score]: Final intent score is {state['intent_score']}")
    return state
