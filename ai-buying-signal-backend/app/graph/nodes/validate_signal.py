from app.graph.state import AgentState

async def validate_signal(state: AgentState) -> dict:
    """Node to deterministically score the buying signal based on intent category."""
    
    category = state.get("intent_category", "UNKNOWN")
    urgency = state.get("urgency", "LOW")
    match_confidence = state.get("service_match_confidence", 0.0)
    
    score = 0
    tier = "LOW"
    
    # Base score determined heavily by the intent category
    if category == "VENDOR_SWITCHING":
        score = 90
    elif category == "EXPLICIT_BUYING_INTENT":
        score = 85
    elif category == "RECOMMENDATION_SEEKING":
        score = 80
    elif category == "HIRING_INTENT":
        score = 75
    elif category == "PROBLEM_SEEKING_SOLUTION":
        score = 65
    else:
        score = 10  # General discussion, news, etc.
        
    # Bump score based on urgency
    if urgency == "HIGH":
        score += 10
    elif urgency == "MEDIUM":
        score += 5
        
    # Scale score based on service match confidence (if they don't match our services, lower the score)
    score = int(score * max(0.5, match_confidence))
    
    # Cap at 100
    score = min(100, score)
    
    # Determine Tier Label
    if score >= 80:
        tier = "HOT"
    elif score >= 60:
        tier = "HIGH"
    elif score >= 40:
        tier = "MEDIUM"
    else:
        tier = "LOW"
        
    return {
        "priority_score": score,
        "tier_label": tier
    }
