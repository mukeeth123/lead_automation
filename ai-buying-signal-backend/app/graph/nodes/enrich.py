import logging
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

async def enrich_node(state: AgentState) -> AgentState:
    raw = state.get("raw_signal", {})
    author = raw.get("author", "Unknown")
    source = raw.get("source", "Unknown")
    
    inferred_profile = "Unknown"
    if author != "Unknown":
        if source == "github": inferred_profile = f"https://github.com/{author}"
        elif source == "reddit": inferred_profile = f"https://reddit.com/user/{author}"
        elif source == "hackernews": inferred_profile = f"https://news.ycombinator.com/user?id={author}"
        elif source == "n8n": inferred_profile = f"https://community.n8n.io/u/{author}"
        
    state["source_profile_url"] = inferred_profile
    logger.info("Node [Enrich]: Enrichment complete")
    return state
