import logging
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

async def persist_node(state: AgentState) -> AgentState:
    """
    Format the final output state. Actual DB persistence is currently handled 
    by the API route (leads.py) after the graph returns.
    """
    logger.info("Node [Persist]: Graph execution complete")
    return state
