from app.graph.state import AgentState
from app.intelligence.identity import IdentityResolutionEngine

engine = IdentityResolutionEngine()

async def resolve_identity(state: AgentState) -> dict:
    """Node to resolve identity of the lead poster."""
    if not state.get("is_qualified"):
        return {}
        
    raw_signal = state.get("raw_signal", {})
    text_content = raw_signal.get("content", "")
    author = raw_signal.get("author", "Unknown")
    
    result = await engine.resolve_identity(text_content, author)
    
    return {
        "company_name": result.company_name,
        "contact_verification": "Enriched" if result.email else "Pending",
        "email": result.email,
        "linkedin_profile": result.linkedin_url,
        "contact_confidence": result.confidence_score,
        "errors": state.get("errors", [])
    }
