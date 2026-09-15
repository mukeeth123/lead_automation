import json
from app.agents.intelligence import call_llm_with_fallback
from app.graph.state import AgentState

async def match_service(state: AgentState) -> dict:
    """Node to evaluate if the detected need aligns with the campaign's core services."""
    
    what_they_want = state.get("what_they_are_looking_for", "")
    problem = state.get("problem_detected", "")
    campaign = state.get("campaign_context", {})
    
    services_offered = campaign.get("core_services", "Software Development, AI Agents, Automation, API Integration")
    target_industries = campaign.get("target_industries", "Any")
    
    prompt = f"""
You are evaluating if a potential client's needs match the services offered by an agency.

Agency Core Services: {services_offered}
Agency Target Industries: {target_industries}

Client's Stated Need: {what_they_want}
Client's Detected Problem: {problem}

Does the agency offer a service that directly solves this client's problem or fulfills their need?

Return ONLY valid JSON matching this schema:
{{
  "service_match": true/false,
  "service_match_confidence": 0.0 to 1.0,
  "ai_summary": "A 1-sentence summary of how the agency can help this specific client based on their problem."
}}
"""
    
    try:
        messages = [{"role": "user", "content": prompt}]
        result_text = await call_llm_with_fallback(messages, temperature=0.0, expect_json=True)
        data = json.loads(result_text)
        
        return {
            "service_match": bool(data.get("service_match", False)),
            "service_match_confidence": float(data.get("service_match_confidence", 0.0)),
            "ai_summary": data.get("ai_summary", "No clear match identified.")
        }
    except Exception as e:
        return {
            "service_match": False,
            "service_match_confidence": 0.0,
            "ai_summary": "Failed to analyze service match.",
            "errors": state.get("errors", []) + [f"Service match failed: {e}"]
        }
