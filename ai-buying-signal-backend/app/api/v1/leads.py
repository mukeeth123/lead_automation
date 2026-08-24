import re
import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.n8n.agent import N8nAgent
from app.agents.indie_hackers.agent import IndieHackersAgent
from app.agents.intelligence import IntelligencePipeline
from typing import List

router = APIRouter()

# In-memory cache to avoid scraping on every request during development
_cached_leads = None

def strip_html(text: str) -> str:
    if not text: return ""
    clean = re.sub(r'<[^>]+>', ' ', text)
    return " ".join(clean.split())

def score_post(text: str) -> int:
    text = text.lower()
    score = 0
    buying = ["buy", "hire", "looking for", "need a", "recommend", "price", "cost", "developer", "agency"]
    pain = ["tired of", "annoyed", "hate", "stuck", "broken", "slow", "hard to", "can't scale"]
    tech = ["ai", "saas", "api", "automation", "integration", "software", "app"]
    
    b_match = sum(1 for k in buying if k in text)
    p_match = sum(1 for k in pain if k in text)
    t_match = sum(1 for k in tech if k in text)
    
    if b_match: score += min(b_match * 10, 40)
    if p_match: score += min(p_match * 5, 20)
    if t_match: score += min(t_match * 5, 25)
    
    if b_match and t_match: score += 10
    if b_match and p_match and t_match: score += 15
    
    return min(score, 100)

@router.get("/leads")
async def get_leads():
    global _cached_leads
    
    if _cached_leads is None:
        # 1. Collect raw signals concurrently
        n8n_agent = N8nAgent()
        ih_agent = IndieHackersAgent()
        
        raw_signals_results = await asyncio.gather(
            n8n_agent.collect(),
            ih_agent.collect(),
            return_exceptions=True
        )
        
        raw_signals = []
        
        # 2. Extract and limit to top 10 from each source evenly
        n8n_res = raw_signals_results[0]
        if not isinstance(n8n_res, Exception):
            raw_signals.extend(n8n_res[:10])
            
        ih_res = raw_signals_results[1]
        if not isinstance(ih_res, Exception):
            raw_signals.extend(ih_res[:10])
        
        # 3. Transform to frontend Lead expectation with fast keyword scoring
        leads = []
        for s in raw_signals:
            clean_content = strip_html(s.content)
            
            # Fast keyword scoring instead of LLM for the main list
            score = score_post(clean_content)
            
            if score >= 85: tier = "HOT"
            elif score >= 60: tier = "HIGH"
            elif score >= 30: tier = "MEDIUM"
            else: tier = "LOW"
            
            leads.append({
                "id": s.external_id,
                "company": s.author or f"{s.source} User",
                "industry": "Software",
                "country": "Global",
                "source": s.source,
                "signalType": "Unknown",
                "technology": "Unknown",
                "businessPain": "Unknown",
                "detectedNeed": "Unknown",
                "intentScore": score,
                "tierLabel": tier,
                "aiSummary": clean_content[:150] + "...", # Placeholder, frontend will use originalSnippet
                "iosysService": "Unknown",
                "publishedDate": s.published_at.isoformat(),
                "daysAgo": 0,
                "status": "New",
                "originalSnippet": clean_content,
                "originalUrl": s.url,
                "explicitRequirement": score >= 40,
                "recentSignal": True,
                "contactEmail": None
            })
        _cached_leads = leads

    return _cached_leads

class AnalyzeRequest(BaseModel):
    title: str
    content: str
    
@router.post("/leads/analyze")
async def analyze_lead(req: AnalyzeRequest):
    pipeline = IntelligencePipeline()
    result = await pipeline.analyze_signal(req.content, req.title)
    return result
