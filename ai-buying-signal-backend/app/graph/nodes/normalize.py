import logging
import re
import html
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

async def normalize_node(state: AgentState) -> AgentState:
    raw = state.get("raw_signal", {})
    content = raw.get("content", "")
    title = raw.get("title", "")
    
    # Strip HTML tags
    clean_content = re.sub(r'<[^>]+>', '', content)
    clean_content = html.unescape(clean_content)
    clean_content = " ".join(clean_content.split())
    
    clean_title = re.sub(r'<[^>]+>', '', title)
    clean_title = html.unescape(clean_title)
    
    state["raw_signal"]["clean_content"] = clean_content[:2000] # Cap length for LLM
    state["raw_signal"]["clean_title"] = clean_title
    
    logger.info("Node [Normalize]: Content normalized")
    return state
