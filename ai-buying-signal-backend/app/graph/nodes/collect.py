import logging
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

async def collect_node(state: AgentState) -> AgentState:
    """
    Ensures the raw signal is present and properly initialized.
    In a fully distributed system, this node might fetch the raw data itself.
    """
    raw = state.get("raw_signal", {})
    if not raw:
        state["errors"] = state.get("errors", []) + ["No raw signal provided"]
        
    logger.info(f"Node [Collect]: Received signal from {raw.get('source', 'Unknown')}")
    return state
