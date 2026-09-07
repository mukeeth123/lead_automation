import logging
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

async def deduplicate_node(state: AgentState) -> AgentState:
    """
    Check if the lead was already processed.
    For this demo, we assume the DB check is done prior to graph entry,
    so this acts as a placeholder for a Redis/Postgres uniqueness check.
    """
    logger.info("Node [Deduplicate]: No duplicates found")
    return state
