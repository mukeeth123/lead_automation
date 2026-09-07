import logging
from typing import Dict, Any
from app.graph.discovery_state import LeadDiscoveryState
from app.api.v1.leads import score_post, score_github_post
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def qualify_lead(state: LeadDiscoveryState) -> LeadDiscoveryState:
    content = state.get("extracted_content", "")
    url_data = state.get("current_url_data", {})
    source = url_data.get("source", "unknown")
    title = url_data.get("title", "")
    industry = state.get("industry", "Any")
    icp = state.get("icp", "Any")
    service = state.get("service", "Any")
    
    if not content:
        return {"is_qualified": False}
        
    prompt = f"""You are a B2B Lead Qualification Engine. 
The user is explicitly looking for leads in the following industry: {industry}
Their Ideal Customer Profile (ICP) is: {icp}
Target Service/Need: {service}

Evaluate the following extracted web page/post content and determine if it is highly relevant to the user's target industry and ICP.
If the post is a job listing or request from a COMPLETELY DIFFERENT industry (e.g. they want Tech but this is Healthcare/Real Estate), score it 0.
If it matches the target industry and shows strong buying/hiring intent, score it 0-100.

Content Title: {title}
Content Source: {source}
Extracted Content: {content[:3000]}

Respond ONLY with valid JSON in the following format:
{{
    "score": <int 0-100>,
    "reasoning": "<short 1 sentence explanation>"
}}
"""

    score = 0
    breakdown = []
    
    try:
        from app.agents.intelligence import call_llm_with_fallback
        import json
        import re
        messages = [{"role": "user", "content": "You return valid JSON.\n" + prompt}]
        response_text = await call_llm_with_fallback(messages, temperature=0.0)
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            score = int(data.get("score", 0))
            breakdown = [f"{score}: {data.get('reasoning', 'Qualified by LLM')}"]
    except Exception as e:
        logger.error(f"Dynamic LLM qualification failed: {e}")
        # Fallback to the old score_post if LLM fails
        from app.api.v1.leads import score_post, score_github_post
        if source == "github":
            score, breakdown = score_github_post(content, title)
        else:
            score, breakdown = score_post(content)

    if score >= 85: tier = "HOT"
    elif score >= 60: tier = "HIGH"
    elif score >= 30: tier = "MEDIUM"
    else: tier = "LOW"
    
    is_qualified = tier != "LOW"
    
    return {
        "is_qualified": is_qualified,
        "score": score,
        "tier": tier,
        "qualification_breakdown": breakdown
    }

def enrich_lead(state: LeadDiscoveryState) -> LeadDiscoveryState:
    if not state.get("is_qualified"):
        return {}
        
    url_data = state.get("current_url_data", {})
    # Simple mock enrichment - in reality this would call Clearbit/OpenCorporates
    enrichment = {
        "company_name": "Unknown",
        "enrichment_source": "none"
    }
    
    return {"enriched_company_info": enrichment}

def save_lead(state: LeadDiscoveryState) -> LeadDiscoveryState:
    if not state.get("is_qualified"):
        return {}
        
    url_data = state.get("current_url_data", {})
    content = state.get("extracted_content", "")
    
    lead = {
        "id": url_data.get("url"),
        "url": url_data.get("url"),
        "author": url_data.get("author", "Unknown"),
        "source": url_data.get("source", "Unknown"),
        "intentScore": state.get("score"),
        "tierLabel": state.get("tier"),
        "scoreBreakdown": state.get("qualification_breakdown"),
        "aiSummary": content[:250] + "...",
        "publishedDate": datetime.now(timezone.utc).isoformat(),
        "status": "New"
    }
    
    return {"saved_leads": [lead]}

def increment_url_index(state: LeadDiscoveryState) -> LeadDiscoveryState:
    idx = state.get("current_url_index", 0)
    return {"current_url_index": idx + 1}
