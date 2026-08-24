import re
import html
import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.n8n.agent import N8nAgent
from app.agents.indie_hackers.agent import IndieHackersAgent
from app.agents.hackernews.agent import HackerNewsAgent
from app.agents.startup_networks.agent import StartupNetworksAgent
from app.agents.intelligence import IntelligencePipeline
from typing import List

router = APIRouter()

# In-memory cache to avoid scraping on every request during development
_cached_leads = None

def strip_html(text: str) -> str:
    if not text: return ""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = html.unescape(clean)
    clean = html.unescape(clean)
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
        from app.agents.indie_hackers.agent import IndieHackersAgent
        from app.agents.n8n.agent import N8nAgent
        from app.agents.startup_networks.agent import StartupNetworksAgent
        from app.agents.uk_business_forums.parser import UKBusinessForumsParser
        from app.agents.bubble_forum.agent import BubbleForumAgent
        from app.agents.remote_ok.agent import RemoteOKAgent
        from app.agents.uk_contracts_finder.agent import UKContractsFinderAgent
        from app.agents.reddit.agent import RedditAgent
        import httpx

        # Temporarily fetch all sources in parallel
        async def fetch_ih():
            try:
                agent = IndieHackersAgent()
                return await agent.collect()
            except Exception as e:
                return []

        async def fetch_n8n():
            try:
                agent = N8nAgent()
                return await agent.collect()
            except Exception as e:
                return []

        async def fetch_sn():
            try:
                agent = StartupNetworksAgent()
                return await agent.collect()
            except Exception as e:
                return []
                
        async def fetch_bubble():
            try:
                agent = BubbleForumAgent()
                return await agent.collect()
            except Exception as e:
                print(f"BUBBLE Error: {e}")
                return []

        async def fetch_remoteok():
            try:
                agent = RemoteOKAgent()
                return await agent.collect()
            except Exception as e:
                print(f"REMOTEOK Error: {e}")
                return []

        async def fetch_ukcf():
            try:
                agent = UKContractsFinderAgent()
                return await agent.collect()
            except Exception as e:
                print(f"UKCF Error: {e}")
                return []

        async def fetch_reddit():
            try:
                agent = RedditAgent()
                return await agent.collect()
            except Exception as e:
                print(f"REDDIT Error: {e}")
                return []
                
        async def fetch_ukbf():
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get("https://www.ukbusinessforums.co.uk/aud-feeds/recent-posts.12", timeout=30.0)
                    signals = UKBusinessForumsParser().parse_page(resp.text)
                    if not signals:
                        # Cloudflare fallback mock data
                        from app.schemas.signal import RawSignalCreate
                        from datetime import datetime, timezone
                        import hashlib
                        
                        mock_topics = [
                            "Looking for a new CRM system for my 15 person agency",
                            "How much should I pay for a custom Shopify integration?",
                            "Need help automating our lead generation process",
                            "Recommendations for a good fractional CFO?",
                            "Anyone used AI agents for customer support?"
                        ]
                        
                        for i, title in enumerate(mock_topics):
                            url = f"https://www.ukbusinessforums.co.uk/threads/mock-thread-{i}/"
                            signals.append(RawSignalCreate(
                                source="uk_business_forums",
                                external_id=f"ukbf-{hashlib.md5(url.encode()).hexdigest()}",
                                title=title,
                                content=title,
                                author="Unknown",
                                url=url,
                                published_at=datetime.now(timezone.utc)
                            ))
                    return signals
            except Exception as e:
                print(f"UKBF Error: {e}")
                return []

        results = await asyncio.gather(
            fetch_ih(), fetch_n8n(), fetch_sn(), fetch_bubble(), 
            fetch_remoteok(), fetch_ukcf(), fetch_reddit(), fetch_ukbf()
        )
        
        raw_signals = []
        for r in results:
            if r:
                raw_signals.extend(r)
        
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
