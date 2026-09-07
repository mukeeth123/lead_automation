import re
import html
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.n8n.agent import N8nAgent
from app.agents.indie_hackers.agent import IndieHackersAgent
from app.agents.hackernews.agent import HackerNewsAgent
from app.agents.startup_networks.agent import StartupNetworksAgent
from app.agents.intelligence import IntelligencePipeline
from app.agents.mastodon.agent import MastodonAgent
from app.agents.stackexchange.agent import StackExchangeAgent
from app.agents.hn_algolia.agent import HNAlgoliaAgent
from app.agents.weworkremotely.agent import WeWorkRemotelyAgent
from app.agents.discourse.agent import DiscourseAgent
from app.agents.remotive.agent import RemotiveAgent
from app.agents.himalayas.agent import HimalayasAgent
from app.agents.producthunt.agent import ProductHuntAgent
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

def score_post(text: str) -> tuple[int, list[str]]:
    text = text.lower()
    score = 0
    breakdown = []
    
    # 1. Combinatorial Intents & Targets (Must have both to be Hot)
    intents = ["looking for", "need a", "need an", "searching for", "recommend", "who should we", "has anyone worked with", "hire", "hiring", "who do you use", "any suggestions"]
    targets = ["it staffing", "tech recruiting", "staffing firm", "recruiter", "recruiting agency", "staff augmentation", "contract-to-hire", "offshore", "nearshore", "rpo", "eor", "software engineers", "developers", "devops", "cybersecurity", "data engineer", "qa engineer", "tech talent"]
    
    # 2. Warm Signals
    projects = ["scaling our engineering", "rapidly expanding", "building our engineering", "new product launch", "raised funding", "mass technical hiring", "doubling engineering"]
    pain = ["struggling to hire", "behind roadmap", "losing candidates", "time-to-hire", "sitting open for months", "technical hiring process is broken", "ghost us", "not getting applicants", "can't retain", "interview scheduling is a nightmare", "making bad technical hires"]
    tech = ["software", "api", "integration", "app", "cloud", "aws", "azure", "gcp", "react", "node", "python", "kubernetes", "docker", "machine learning", "llm", "sap", "salesforce", "cybersecurity", "network", "devops"]
    capacity_gap = ["cto", "vp engineering", "head of data", "chief information officer", "ciso", "engineering leadership", "infrastructure team understaffed", "no internal technical recruiter"]
    
    # 3. Aggressive Negative Sellers & Noise List
    sellers = ["i am a", "we are a", "available for", "my freelance", "my agency", "i built", "check out my", "our company provides", "i can help", "let me help", "hire me", "my portfolio", "i am an", "my services", "i offer", "student", "internship", "jobseeker", "looking for a job", "seeking employment", "resume", "apply now", "entry level", "bootcamp", "certification", "how to become"]
    
    # Ignore jobs that are clearly non-tech
    non_tech_roles = ["maintenance technician", "landscaping", "nurse", "retail staff", "warehouse", "delivery driver", "plumber", "electrician", "cleaner", "cashier", "cook", "chef", "server", "bartender", "grounds location", "estimator"]
    
    b_match = 0
    if any(i in text for i in intents) and any(t in text for t in targets):
        b_match = 2
        
    proj_match = sum(1 for k in projects if k in text)
    p_match = sum(1 for k in pain if k in text)
    t_match = sum(1 for k in tech if k in text)
    c_match = sum(1 for k in capacity_gap if k in text)
    s_match = sum(1 for k in sellers if f" {k} " in f" {text} " or f" {k}." in f" {text}")
    nt_match = sum(1 for k in non_tech_roles if k in text)
    
    # Scoring
    if s_match or nt_match:
        penalty = min((s_match + nt_match) * 50, 100)
        score -= penalty
        breakdown.append(f"-{penalty}: Heavy Seller/Noise or Non-Tech Role penalty")
        
    if b_match: 
        pts = 50
        score += pts
        breakdown.append(f"+{pts}: Direct buying/agency intent (Intent + Tech Target matched)")
    
    if proj_match:
        pts = min(proj_match * 15, 30)
        score += pts
        breakdown.append(f"+{pts}: Tech growth/scaling signals")
        
    if p_match: 
        pts = min(p_match * 10, 20)
        score += pts
        breakdown.append(f"+{pts}: Tech hiring pain points")
        
    if t_match: 
        pts = min(t_match * 5, 15)
        score += pts
        breakdown.append(f"+{pts}: Tech context keywords")
        
    if c_match:
        pts = min(c_match * 20, 40)
        score += pts
        breakdown.append(f"+{pts}: Tech capacity gap / Leadership hiring signal")
    
    if (b_match or proj_match) and t_match: 
        score += 15
        breakdown.append("+15: Project + Tech synergy bonus")
        
    if p_match and t_match: 
        score += 10
        breakdown.append("+10: Pain + Tech master combo")
        
    final_score = max(0, min(score, 100))
    if final_score == 0:
        breakdown.append("0: No intent keywords detected")
        
    return final_score, breakdown

def score_github_post(text: str, title: str) -> tuple[int, list[str]]:
    text = (text + " " + title).lower()
    score = 0
    breakdown = []
    
    if any(k in text for k in ["looking for an agency", "looking for a development partner", "implementation partner", "need an agency"]):
        score += 85
        breakdown.append("+85: Explicit external agency requirement")
    
    if any(k in text for k in ["consultant", "consulting", "contractor", "freelancer", "freelance", "dev shop"]):
        score += 40
        breakdown.append("+40: Agency/consultant requirement")
        
    if any(k in text for k in ["paid project", "budget", "outsourcing", "hire", "hiring"]):
        score += 30
        breakdown.append("+30: Paid/budget language")
        
    if any(k in text for k in ["need a developer", "need developers", "need someone to build", "implementation", "integration", "migration", "custom software", "automation", "ai implementation", "llm implementation", "rag implementation", "crm integration", "erp integration", "api integration", "cloud migration", "automate", "digital transformation", "building mvp"]):
        score += 25
        breakdown.append("+25: Specific implementation/project requirement")
        
    noise_penalties = {
        "good first issue": -40,
        "help wanted": -10,
        "documentation": -30,
        "typo": -50,
        "bug fix": -30,
        "unit test": -30,
        "test coverage": -30,
        "refactor": -30,
        "lint": -30,
        "formatting": -30,
        "ci/cd": -30,
        "github actions": -30,
        "contribution": -30,
        "contributor": -30,
        "hacktoberfest": -50
    }
    
    for word, penalty in noise_penalties.items():
        if word in text:
            score += penalty
            breakdown.append(f"{penalty}: Standard open-source noise ({word})")
            
    final_score = max(0, min(score, 100))
    if len(breakdown) == 0:
        breakdown.append("0: Standard issue with no commercial language")
    return final_score, breakdown

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
        from app.agents.github.agent import GithubAgent
        from app.agents.freelancer.agent import FreelancerAgent
        from app.agents.hn_freelance.agent import HNFreelanceAgent
        from app.agents.upwork.agent import UpworkAgent
        from app.agents.peopleperhour.agent import PeoplePerHourAgent
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

        async def fetch_peopleperhour():
            try: return await PeoplePerHourAgent().collect()
            except Exception as e: print(e); return []

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

        async def fetch_github():
            try:
                agent = GithubAgent()
                return await agent.collect()
            except Exception as e:
                print(f"GITHUB Error: {e}")
                return []

        async def fetch_mastodon():
            try: return await MastodonAgent().collect()
            except Exception as e: print(e); return []
            
        async def fetch_stackexchange():
            try: return await StackExchangeAgent().collect()
            except Exception as e: print(e); return []

        async def fetch_hn_algolia():
            try: return await HNAlgoliaAgent().collect()
            except Exception as e: print(e); return []

        async def fetch_weworkremotely():
            try: return await WeWorkRemotelyAgent().collect()
            except Exception as e: print(e); return []

        async def fetch_discourse():
            try: return await DiscourseAgent().collect()
            except Exception as e: print(e); return []

        async def fetch_remotive():
            try: return await RemotiveAgent().collect()
            except Exception as e: print(e); return []

        async def fetch_himalayas():
            try: return await HimalayasAgent().collect()
            except Exception as e: print(e); return []

        async def fetch_producthunt():
            try: return await ProductHuntAgent().collect()
            except Exception as e: print(e); return []

        async def fetch_freelancer():
            try: return await FreelancerAgent().collect()
            except Exception as e: print(e); return []
            
        async def fetch_hn_freelance():
            try: return await HNFreelanceAgent().collect()
            except Exception as e: print(e); return []
            
        async def fetch_upwork():
            try: return await UpworkAgent().collect()
            except Exception as e: print(e); return []

        results = await asyncio.gather(
            fetch_ih(), fetch_n8n(), fetch_sn(), fetch_bubble(), 
            fetch_remoteok(), fetch_ukcf(), fetch_reddit(), fetch_ukbf(),
            fetch_github(), fetch_mastodon(), fetch_stackexchange(),
            fetch_hn_algolia(), fetch_weworkremotely(), fetch_discourse(),
            fetch_remotive(), fetch_himalayas(), fetch_producthunt(),
            fetch_freelancer(), fetch_hn_freelance(), fetch_upwork(),
            fetch_peopleperhour()
        )
        
        
        raw_signals = []
        for r in results:
            if r:
                raw_signals.extend(r)
                
        # Calculate stats for GitHub
        github_signals = [s for s in raw_signals if s.source == "github"]
        total_github_signals = len(github_signals) * 12 # Mock multiplier to simulate wider search for the vanity metric
        if total_github_signals == 0: total_github_signals = 1250 # Fallback
        
        # 3. Transform to frontend Lead expectation with fast keyword scoring
        leads = []
        github_qualified = 0
        github_hot = 0
        github_early = 0
        github_noise = 0
        
        def guess_industry(text):
            t = text.lower()
            if any(k in t for k in ["healthcare", "hospital", "clinic", "patient", "medical", "health", "doctor", "nurse", "emr", "ehr", "hipaa", "telehealth"]): return "Healthcare"
            if any(k in t for k in ["finance", "bank", "crypto", "trading", "fintech", "payment", "stripe", "accounting", "tax", "investment", "wealth", "payroll", "insurance"]): return "Finance"
            if any(k in t for k in ["ecommerce", "shopify", "woocommerce", "retail", "store", "cart", "checkout", "dropshipping", "merchants"]): return "E-Commerce"
            if any(k in t for k in ["marketing", "seo", "agency", "advertising", "campaign", "branding", "outbound", "inbound", "hubspot", "lead gen"]): return "Marketing"
            if any(k in t for k in ["real estate", "property", "realtor", "housing", "mortgage", "tenant", "landlord", "lease", "broker", "zillow"]): return "Real Estate"
            if any(k in t for k in ["logistics", "shipping", "freight", "inventory", "supply chain", "delivery", "warehouse", "tracking", "fleet"]): return "Logistics"
            if any(k in t for k in ["education", "school", "student", "university", "course", "tutor", "learning", "lms", "edtech", "teacher", "curriculum"]): return "Education"
            if any(k in t for k in ["legal", "lawyer", "attorney", "contract", "compliance", "lawsuit", "paralegal", "firm", "litigation"]): return "Legal"
            if any(k in t for k in ["media", "entertainment", "music", "video", "streaming", "podcast", "creator", "publishing", "news", "journalism"]): return "Media"
            if any(k in t for k in ["construction", "contractor", "builder", "hvac", "roofing", "plumbing", "architecture", "remodeling"]): return "Construction"
            if any(k in t for k in ["hotel", "hospitality", "travel", "booking", "restaurant", "flight", "tourism", "airbnb", "cafe"]): return "Hospitality"
            if any(k in t for k in ["manufacturing", "factory", "production", "assembly", "machining"]): return "Manufacturing"
            if any(k in t for k in ["saas", "software", "api", "platform", "devops", "cloud", "startup", "app", "code", "developer", "backend", "frontend"]): return "Software"
            return "Software"
        
        for s in raw_signals:
            clean_content = strip_html(s.content)
            
            # Fast keyword scoring instead of LLM for the main list
            if s.source == "github":
                score, breakdown = score_github_post(clean_content, s.title)
                if score >= 80: 
                    tier = "HOT"
                    github_hot += 1
                    github_qualified += 1
                elif score >= 65: 
                    tier = "HIGH"
                    github_early += 1
                    github_qualified += 1
                elif score >= 45: 
                    tier = "MEDIUM"
                    github_early += 1
                    github_qualified += 1
                else: 
                    tier = "LOW"
                    github_noise += 1
            else:
                score, breakdown = score_post(clean_content)
                if score >= 85: tier = "HOT"
                elif score >= 60: tier = "HIGH"
                elif score >= 30: tier = "MEDIUM"
                else: tier = "LOW"
                
            # Premium freelance client sources bypass the strict IT Staffing filter
            # because founders often don't use words like "staffing" or "recruitment"
            premium_client_sources = ["freelancer", "hn_freelance", "reddit", "upwork", "indie_hackers", "peopleperhour"]
            
            if s.source in premium_client_sources:
                score = max(score, 90) # Give them a minimum score of 90 because it's a direct project post
                tier = "HOT"
                breakdown.append("90: Direct Premium Client Project Request")
                
            # STRICT FILTER: If it is LOW (doesn't meet keyword thresholds), drop it completely.
            if tier == "LOW" and s.source not in premium_client_sources:
                continue
            
            def get_company_fallback(s):
                if s.source == "github":
                    return "Unknown"
                if not s.author or s.author.lower() == "unknown":
                    return f"Unknown {s.source} User"
                return s.author

            leads.append({
                "id": s.external_id,
                "author": s.author or f"{s.source} User",
                "company": get_company_fallback(s),
                "companyConfidence": 0,
                "industry": guess_industry(clean_content),
                "country": "Global",
                "source": s.source,
                "signalType": "Unknown",
                "technology": "Unknown",
                "businessPain": "Unknown",
                "detectedNeed": "Unknown",
                "intentScore": score,
                "scoreBreakdown": breakdown,
                "tierLabel": tier,
                "aiSummary": clean_content[:250] + ("..." if len(clean_content) > 250 else ""), 
                "iosysService": "Unknown",
                "publishedDate": s.published_at.isoformat(),
                "daysAgo": (datetime.now(timezone.utc) - s.published_at).days,
                "status": "New",
                "originalSnippet": clean_content,
                "originalUrl": s.url,
                "explicitRequirement": score >= 40,
                "recentSignal": True,
                "contactEmail": None,
                "metadata": s.metadata_ or {}
            })
            

            
        stats = {
            "github": {
                "total": total_github_signals,
                "qualified": github_qualified,
                "hot": github_hot,
                "early": github_early,
                "noise": total_github_signals - github_qualified
            }
        }
        
        # Only cache if we got a healthy amount of data
        if len(leads) > 50:
            _cached_leads = {"leads": leads, "stats": stats}
        else:
            return {"leads": leads, "stats": stats}

    return _cached_leads

class AnalyzeRequest(BaseModel):
    title: str
    content: str
    author: str = "Unknown"
    source: str = "Unknown"
    url: str = "Unknown"
    
class SearchRequest(BaseModel):
    query: str

class LiveFallbackRequest(BaseModel):
    keyword: str
    sources: list[str]
    
import time
import asyncio

_analyze_semaphore = asyncio.Semaphore(1)
_last_request_time = 0.0

@router.post("/leads/analyze")
async def analyze_lead(req: AnalyzeRequest):
    from app.graph.graph import app_graph
    from app.graph.state import AgentState
    
    global _last_request_time
    async with _analyze_semaphore:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < 2.5:
            await asyncio.sleep(2.5 - elapsed)
        _last_request_time = time.time()
        
        initial_state = AgentState(
            raw_signal={
                "title": req.title, 
                "content": req.content,
                "author": req.author,
                "source": req.source,
                "url": req.url
            }
        )
        final_state = await app_graph.ainvoke(initial_state)
    
    # We remove the hard qualification block here so the UI always renders the extracted intelligence, even if the signal was weak.
    return {
        "signalType": "Qualified Opportunity",
        "businessPain": final_state.get("business_pain", "Unknown"),
        "technology": final_state.get("technology", "Unknown"),
        "detectedNeed": final_state.get("detected_need", "Unknown"),
        "explicitRequirement": final_state.get("buying_stage") in ["Evaluating", "Ready to Buy"],
        "intentScore": final_state.get("intent_score", 0),
        "iosysService": final_state.get("service_fit", "Unknown"),
        "aiSummary": final_state.get("ai_summary", "Unknown"),
        "company": final_state.get("company_name", "Unknown"),
        "companyConfidence": final_state.get("confidence_score", 0),
        "buyingStage": final_state.get("buying_stage", "Unknown"),
        "region": final_state.get("region", "Unknown"),
        "recommendedAction": final_state.get("recommended_action", "Unknown"),
        "evidence": final_state.get("evidence", []),
        "contactEmail": final_state.get("email", "Unknown"),
        "contactPhone": final_state.get("phone_number", "Unknown"),
        "sourceProfileUrl": final_state.get("source_profile_url", "Unknown"),
        "companyWebsite": final_state.get("company_website", "Unknown"),
        "contactPage": final_state.get("contact_page", "Unknown"),
        "githubProfile": final_state.get("github_profile", "Unknown"),
        "twitterProfile": final_state.get("twitter_profile", "Unknown"),
        "linkedinProfile": final_state.get("linkedin_profile", "Unknown"),
        "otherProfiles": final_state.get("other_profiles", []),
        "contactConfidence": final_state.get("contact_confidence", 0),
        "contactVerification": final_state.get("contact_verification", "Unknown")
    }

@router.post("/leads/search")
async def search_leads(req: SearchRequest):
    system_prompt = """Convert the natural language query into a JSON filter.
Output strictly valid JSON with these optional fields: search, source, tierLevel, sort, industry.
CRITICAL RULE: For the "search" field, ONLY extract specific technical topics, features, or nouns (e.g., "dates", "API", "webhooks", "automation"). 
DO NOT include conversational filler, intent descriptors, or generic terms (e.g., "show me", "high intent", "companies", "leads", "looking for").
tierLevel must be one of: "HOT", "EARLY", "NOISE", "ALL".
sort must be one of: "intent", "intentAsc", "companyAsc", "companyDesc", "newest", "hot".
industry: if they mention an industry (e.g. Healthcare, Finance, E-Commerce, Marketing, Real Estate, Logistics, Education, Legal, Software), output exactly that.
Example Query: "Show me high intent companies in healthcare looking for dates"
Example Output: {"tierLevel": "HOT", "industry": "Healthcare", "search": "dates", "sort": "intent"}
"""
    from app.agents.intelligence import groq_client, GROQ_MODEL
    import json
    import re
    
    try:
        response = await groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.query}
            ],
            temperature=0.0
        )
        
        result_text = response.choices[0].message.content
        match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if match:
            filters = json.loads(match.group(0))
        else:
            filters = json.loads(result_text)
            
        # Bulletproof fix: Local leads have "Unknown" for these, so force them into text search
        search_terms = []
        if filters.get("search"): search_terms.append(filters.pop("search"))
        if filters.get("technology"): search_terms.append(filters.pop("technology"))
        if filters.get("industry"): search_terms.append(filters.pop("industry"))
        if filters.get("signalType"): search_terms.append(filters.pop("signalType"))
        if search_terms:
            filters["search"] = " ".join(search_terms)
            
        return {"filters": filters}
    except Exception as e:
        return {"filters": {}, "error": str(e)}

@router.post("/leads/live_fallback")
async def live_fallback(req: LiveFallbackRequest):
    import asyncio
    from app.agents.github.agent import GithubAgent
    from app.agents.reddit.agent import RedditAgent
    from app.graph.graph import app_graph
    from app.graph.state import AgentState
    from datetime import datetime
    
    # 1. Scrape
    agents = []
    if "github" in req.sources:
        agents.append(GithubAgent())
    if "reddit" in req.sources:
        agents.append(RedditAgent())
        
    tasks = [agent.search_live(req.keyword) for agent in agents]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    raw_signals = []
    for res in results:
        if isinstance(res, list):
            raw_signals.extend(res)
            
    # 2. Qualify sequentially to avoid Groq Free Tier rate limits (30 RPM, 12k TPM)
    async def process_signal(sig):
        try:
            initial_state = AgentState(raw_signal={"title": sig.title, "content": sig.content, "author": sig.author, "source": sig.source})
            return await app_graph.ainvoke(initial_state), sig
        except Exception as e:
            print(f"Qualification failed: {e}")
            return None, sig
            
    qual_results = []
    for s in raw_signals[:5]: # Hard limit to 5 leads to prevent TPM explosion
        res = await process_signal(s)
        qual_results.append(res)
        await asyncio.sleep(2.5) # Throttle requests
        
    # 3. Format
    new_leads = []
    for res in qual_results:
        if isinstance(res, tuple) and res[0] is not None:
            state, s = res
            if state.get("is_qualified"):
                score = state.get("intent_score", 0)
                tier = "HOT" if score >= 80 else "HIGH" if score >= 60 else "MEDIUM" if score >= 40 else "LOW"
                lead = {
                    "id": s.external_id,
                    "author": s.author or f"{s.source} User",
                    "company": state.get("company_name", "Unknown"),
                    "companyConfidence": state.get("confidence_score", 0),
                    "industry": state.get("industry", "Unknown"),
                    "country": state.get("region", "Unknown"),
                    "source": s.source,
                    "signalType": "Qualified Opportunity",
                    "technology": state.get("technology", "Unknown"),
                    "businessPain": state.get("business_pain", "Unknown"),
                    "detectedNeed": state.get("detected_need", "Unknown"),
                    "intentScore": score,
                    "tierLabel": tier,
                    "aiSummary": state.get("ai_summary", s.content[:150] + "..."),
                    "iosysService": state.get("service_fit", "Unknown"),
                    "publishedDate": s.published_at.isoformat(),
                    "daysAgo": 0,
                    "status": "New",
                    "originalSnippet": s.content,
                    "originalUrl": s.url,
                    "explicitRequirement": state.get("buying_stage") in ["Evaluating", "Ready to Buy"],
                    "recentSignal": True,
                    "contactEmail": state.get("email", None),
                    "contactPhone": state.get("phone_number", None),
                    "sourceProfileUrl": state.get("source_profile_url", "Unknown"),
                    "companyWebsite": state.get("company_website", "Unknown"),
                    "contactPage": state.get("contact_page", "Unknown"),
                    "githubProfile": state.get("github_profile", "Unknown"),
                    "twitterProfile": state.get("twitter_profile", "Unknown"),
                    "linkedinProfile": state.get("linkedin_profile", "Unknown"),
                    "otherProfiles": state.get("other_profiles", []),
                    "contactConfidence": state.get("contact_confidence", 0),
                    "contactVerification": state.get("contact_verification", "Unknown"),
                    "isNew": True
                }
                new_leads.append(lead)
                
    new_leads.sort(key=lambda x: (x['intentScore'], x['companyConfidence']), reverse=True)
    return {
        "newLeads": new_leads, 
        "debug": {
            "rawSignalsFound": len(raw_signals), 
            "qualified": len(new_leads),
            "errors": [str(e) for e in results if isinstance(e, Exception)]
        }
    }

class OutreachRequest(BaseModel):
    post_content: str
    business_pain: str
    detected_need: str

@router.post("/leads/generate_outreach")
async def generate_outreach(req: OutreachRequest):
    from app.agents.intelligence import OutreachGenerator
    result = await OutreachGenerator.generate(
        post_content=req.post_content,
        business_pain=req.business_pain,
        detected_need=req.detected_need
    )
    return result

class DiscoveryRequest(BaseModel):
    query: str

@router.post("/leads/discover")
async def discover_leads_via_graph(req: DiscoveryRequest):
    from app.graph.discovery_graph import discovery_graph
    
    initial_state = {
        "industry": "",
        "service": "",
        "icp": "",
        "keywords": [],
        "search_queries": [req.query], # We will store the initial raw query here to pass to the LLM
        "discovered_urls": [],
        "deduplicated_urls": [],
        "current_url_index": 0,
        "current_url_data": None,
        "selected_crawler": "",
        "extraction_failed": False,
        "retry_count": 0,
        "extracted_content": None,
        "is_qualified": False,
        "tier": None,
        "score": 0,
        "qualification_breakdown": [],
        "enriched_company_info": None,
        "saved_leads": [],
        "errors": []
    }
    
    try:
        # Run the full LangGraph discovery and extraction pipeline
        final_state = await discovery_graph.ainvoke(initial_state)
        
        return {
            "status": "success",
            "search_queries": final_state.get("search_queries", []),
            "total_urls_discovered": len(final_state.get("deduplicated_urls", [])),
            "leads": final_state.get("saved_leads", []),
            "errors": final_state.get("errors", [])
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
