import logging
from typing import Dict, Any
from app.graph.discovery_state import LeadDiscoveryState
from app.api.v1.leads import score_post, score_github_post
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def static_pre_filter(text: str) -> tuple[bool, str]:
    """Fast regex/substring filter to drop obvious noise before calling the LLM."""
    text_lower = text.lower()
    
    # 1. Reject Seller noise (agencies, freelancers promoting themselves)
    sellers = [
        "we built an", "i started an", "how to start an", "check out our",
        "i am a", "we are a", "available for", "my freelance", "my agency",
        "i built", "check out my", "our company provides", "i can help",
        "let me help", "hire me", "my portfolio", "i am an", "my services",
        "i offer", "we offer", "our services", "services we provide"
    ]
    for s in sellers:
        if s in text_lower:
            return False, f"Static Reject: Seller noise detected ('{s}')"
            
    # 2. Reject Co-founder / Partner noise
    partners = [
        "looking for a co-founder", "looking for a cofounder",
        "looking for a business partner", "need a co-founder",
        "seeking a cofounder", "seeking a business partner"
    ]
    for p in partners:
        if p in text_lower:
            return False, f"Static Reject: Co-founder/Partner search ('{p}')"
            
    # 3. Reject Educational / News noise
    edu_news = [
        "is changing the industry", "tools you should use", "how i automated",
        "tutorial", "guide on how to", "my journey building",
        "ask hn: what do you think", "what do you guys think about"
    ]
    for e in edu_news:
        if e in text_lower:
            return False, f"Static Reject: Educational/News/Discussion ('{e}')"
            
    # 4. Reject Explicitly Excluded Services
    excluded = [
        "seo", "social media marketing", "content writing", "meta ads",
        "google ads", "ppc", "influencer marketing", "video editing",
        "video creation", "voice acting", "graphic design", "recruitment",
        "accounting", "legal services", "real estate services", "virtual assistant"
    ]
    
    # We require a bit more boundary checking for short terms like "seo" to avoid matching inside words
    import re
    for ex in excluded:
        pattern = r'\b' + re.escape(ex) + r'\b'
        if re.search(pattern, text_lower):
            # If the post contains heavily excluded terms and doesn't explicitly mention dev/software, reject it immediately
            if not any(dev_term in text_lower for dev_term in ["software", "app", "developer", "development", "saas", "api"]):
                return False, f"Static Reject: Excluded service detected ('{ex}')"

    # 5. Reject India / South-Asia geo-targeted posts
    india_signals = [
        "delhi ncr", "delhi/ncr", "people based in india", "india only", "indian only",
        "based in india", "located in india", "india-based", "mumbai based", "bangalore based",
        "hyderabad based", "pune based", "chennai based", "kolkata based",
        "for indians only", "india location", "india candidates",
        "₹", "inr", "rupees", "rs.", "rs "
    ]
    for sig in india_signals:
        if sig in text_lower:
            return False, f"Static Reject: India-targeted content ('{sig}')"
            
    # If it passed all negative filters, we allow it to proceed to the LLM
    return True, "Passed static pre-filter"


async def qualify_lead(state: LeadDiscoveryState) -> LeadDiscoveryState:
    content = state.get("extracted_content", "")
    url_data = state.get("current_url_data", {})
    source = url_data.get("source", "unknown")
    title = url_data.get("title", "")
    campaign_name = state.get("campaign_name", "Unknown")
    
    if not content:
        return {"is_qualified": False, "score": 0, "tier": "LOW", "qualification_breakdown": ["No content"]}
        
    # STAGE 1: Static Pre-Filter
    passed, reason = static_pre_filter(content)
    if not passed:
        return {
            "is_qualified": False,
            "score": 0,
            "tier": "LOW",
            "qualification_breakdown": [f"0: {reason}"]
        }
        
    # STAGE 2: Removed automated LLM Validation
    # We now immediately save leads that passed the static filter as PENDING_AI 
    # to avoid rate limits during mass discovery.
    
    score = 50
    tier = "PENDING_AI"
    breakdown = ["Passed static filter. Waiting for manual AI deep qualification."]
    is_qualified = True
    
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
