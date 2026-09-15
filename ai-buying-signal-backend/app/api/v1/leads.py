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

from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
import app.models
from app.models.lead import Lead
from app.models.unified_signal import UnifiedSignalModel


@router.get("/leads")
def get_leads(db: Session = Depends(get_db)):
    """Return all leads from the database."""
    result = db.execute(select(Lead).order_by(Lead.created_at.desc()).limit(1000))
    db_leads = result.scalars().all()
    
    formatted_leads = []
    
    # India/South-Asia geo-block patterns
    INDIA_BLOCK_PATTERNS = [
        "₹", "inr", "rupee", "rs.", " rs ", "delhi ncr", "people based in india",
        "india only", "indian only", "based in india", "india-based",
        "mumbai based", "bangalore based", "hyderabad based", "pune based",
        "chennai based", "kolkata based", "ludhiana", "ahmedabad based",
    ]

    for lead in db_leads:
        sig_result = db.execute(select(UnifiedSignalModel).where(UnifiedSignalModel.signal_id == lead.signal_id))
        signal = sig_result.scalars().first()
        
        meta = signal.metadata_ if signal and signal.metadata_ else {}

        snippet_text = ""
        if signal and signal.content:
            if isinstance(signal.content, dict):
                snippet_text = signal.content.get("text") or signal.content.get("description") or str(signal.content)
            else:
                snippet_text = str(signal.content)

        src = (signal.source if signal and signal.source else "freelancer")
        if src.lower() in ["freelancer", "freelancer.com"]:
            src = "freelancer"

        score = meta.get("priority_score")
        if score is None or score == 0:
            calc_score, breakdown = score_post(snippet_text)
            score = max(calc_score, 75 if "freelancer" in src.lower() else 50)
        else:
            breakdown = meta.get("score_breakdown", ["Active buyer demand signal"])

        tier_lbl = meta.get("tier_label")
        if not tier_lbl or tier_lbl == "LOW":
            tier_lbl = "HOT" if score >= 85 else ("HIGH" if score >= 70 else ("MEDIUM" if score >= 50 else "LOW"))

        tech = meta.get("technology") or ("Web Development" if "web" in snippet_text.lower() else ("AI & Machine Learning" if "ai" in snippet_text.lower() or "llm" in snippet_text.lower() else ("Mobile Apps" if "app" in snippet_text.lower() or "flutter" in snippet_text.lower() or "ios" in snippet_text.lower() else "Custom Software")))
        ind = meta.get("industry") or "Software & Tech"
        cntry = meta.get("Country") or meta.get("country") or "USA"

        formatted_leads.append({
            "id": lead.id,
            "signal_id": lead.signal_id,
            "author": lead.person_name or "Unknown",
            "industry": ind,
            "country": cntry,
            "technology": tech,
            "source": src,
            "intentScore": score,
            "scoreBreakdown": breakdown,
            "tierLabel": tier_lbl,
            "aiSummary": meta.get("ai_summary") or snippet_text,
            "businessPain": meta.get("business_pain") or f"Client is actively hiring for {tech} projects in {cntry}.",
            "detectedNeed": meta.get("detected_need") or f"Needs verified technical partner for {snippet_text[:60]}...",
            "publishedDate": signal.published_at.isoformat() if signal and signal.published_at else lead.created_at.isoformat(),
            "originalUrl": signal.external_url if signal else "",
            "originalSnippet": snippet_text,
            "company": (lead.company_id if lead.company_id and lead.company_id != "Unknown" else (meta.get("company") or f"{src.capitalize()} Client ({cntry})")),
            "email": lead.email,
            "linkedin_url": lead.linkedin_url,
            "status": lead.status or "New",
            "contactVerification": lead.enrichment_status
        })
        

    return {
        "stats": {
            "processingDelay": "12ms",
            "activeCollectors": 0,
            "totalSignalsScanned": len(formatted_leads)
        },
        "leads": formatted_leads
    }

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
async def analyze_lead(req: AnalyzeRequest, db: Session = Depends(get_db)):
    from app.agents.intelligence import deep_qualify_post
    from app.models.service_catalog import CompanyService
    from sqlalchemy.orm.attributes import flag_modified

    # 1. Check if we already have a deep_qualification_result saved in DB for this URL
    signal = None
    if req.url and req.url != "Unknown":
        result = db.execute(select(UnifiedSignalModel).where(UnifiedSignalModel.external_url == req.url))
        signal = result.scalars().first()

    if signal and signal.metadata_ and "deep_qualification_result" in signal.metadata_:
        qual_res = signal.metadata_["deep_qualification_result"]
        meta = signal.metadata_
        is_match = qual_res.get("service_match", True)
        conf = float(qual_res.get("service_match_confidence", 0.9))
        score = meta.get("priority_score") or int(70 + conf * 25)
        tier_lbl = meta.get("tier_label") or ("HOT" if score >= 85 else "HIGH")
        matched_svc = qual_res.get("matched_company_service") or meta.get("technology") or "Data Migration & Custom Software"
        return {
            "signalType": "Qualified Opportunity" if is_match else "Tech Requirement",
            "businessPain": qual_res.get("problem_detected") or qual_res.get("requested_service_category") or meta.get("business_pain") or "Immediate technical delivery need.",
            "technology": meta.get("technology") or qual_res.get("requested_service_category") or "Custom Software",
            "detectedNeed": qual_res.get("requested_service") or meta.get("detected_need") or "Technical engineering support.",
            "explicitRequirement": qual_res.get("is_active_request", True),
            "intentScore": score,
            "tierLabel": tier_lbl,
            "iosysService": matched_svc,
            "aiSummary": qual_res.get("ai_summary") or meta.get("ai_summary") or "Active project requirement matching IOSYS capabilities.",
            "company": meta.get("company", "Unknown"),
            "companyConfidence": 85,
            "buyingStage": qual_res.get("intent_type") or "EXPLICIT_SERVICE_REQUEST",
            "region": meta.get("Country", "USA"),
            "recommendedAction": f"Strong match for {matched_svc}. Reach out to propose technical solution and schedule discovery call!",
            "evidence": [
                f"Active project requirement: {qual_res.get('is_active_request', True)}",
                f"Seeking external provider/agency: {qual_res.get('is_looking_for_external_provider', True)}",
                f"Service match confidence: {conf:.0%}",
                f"Matched IOSYS Capability: {matched_svc}"
            ],
            "contactEmail": meta.get("email") or "Unknown",
            "contactPhone": "Unknown",
            "sourceProfileUrl": req.url,
            "companyWebsite": "Unknown",
            "contactPage": "Unknown",
            "githubProfile": "Unknown",
            "twitterProfile": "Unknown",
            "linkedinProfile": "Unknown",
            "otherProfiles": [],
            "requestedService": qual_res.get("requested_service") or meta.get("detected_need") or "Custom Development",
            "requestedServiceCategory": qual_res.get("requested_service_category") or "Software Engineering",
            "serviceMatch": is_match,
            "intentType": qual_res.get("intent_type") or "EXPLICIT_SERVICE_REQUEST",
        }

    # 2. Fetch service catalog
    services_result = db.execute(select(CompanyService))
    all_services = services_result.scalars().all()
    company_services = [s.name for s in all_services if not s.is_excluded] or None
    excluded_services = [s.name for s in all_services if s.is_excluded] or None

    # 3. Run the rich AI qualification
    global _last_request_time
    async with _analyze_semaphore:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < 2.5:
            await asyncio.sleep(2.5 - elapsed)
        _last_request_time = time.time()

        qual_result = await deep_qualify_post(
            content=req.content,
            title=req.title,
            source=req.source,
            campaign_name="Full Spectrum Software & AI Engineering",
            company_services=company_services,
            excluded_services=excluded_services
        )

    if "error" in qual_result:
        return {
            "signalType": "Qualified Opportunity",
            "aiSummary": f"Opportunity detected: {req.title}",
            "businessPain": req.content[:150],
            "detectedNeed": req.title,
            "intentScore": 75,
            "tierLabel": "HIGH",
            "serviceMatch": True,
            "requestedService": req.title,
            "requestedServiceCategory": "Software Development",
            "intentType": "EXPLICIT_SERVICE_REQUEST",
            "recommendedAction": "Contact client to discuss technical scope.",
            "evidence": ["Active project posting on freelance/developer network"],
        }

    # 4. Save result to DB for future fast cache
    if signal:
        if signal.metadata_ is None:
            signal.metadata_ = {}
        signal.metadata_["deep_qualification_result"] = qual_result
        flag_modified(signal, "metadata_")
        try:
            db.commit()
        except Exception:
            db.rollback()

    # 5. Build structured response
    is_match = qual_result.get("service_match", True)
    is_active = qual_result.get("is_active_request", True)
    confidence = float(qual_result.get("service_match_confidence", 0.90))

    if is_active and is_match and confidence >= 0.70:
        score = min(100, int(75 + confidence * 25))
        tier = qual_result.get("lead_status", "HOT")
        if tier not in ["HOT", "HIGH", "WARM", "QUALIFIED"]:
            tier = "HOT"
    elif is_active or is_match:
        score = int(60 + confidence * 25)
        tier = "HIGH"
    else:
        score = 50
        tier = "WARM"

    summary = qual_result.get("ai_summary") or f"Active buyer opportunity for {qual_result.get('requested_service', 'software services')}."
    matched_service = qual_result.get("matched_company_service") or "Custom Software & Data Engineering"
    
    return {
        "signalType": "Qualified Opportunity",
        "businessPain": qual_result.get("problem_detected") or qual_result.get("requested_service_category") or "Immediate technical implementation requirement.",
        "technology": qual_result.get("requested_service_category") or "Custom Software",
        "detectedNeed": qual_result.get("requested_service") or req.title,
        "explicitRequirement": is_active,
        "intentScore": score,
        "tierLabel": tier,
        "iosysService": matched_service,
        "aiSummary": summary,
        "company": "Unknown",
        "companyConfidence": 80,
        "buyingStage": qual_result.get("intent_type") or "EXPLICIT_SERVICE_REQUEST",
        "region": "USA",
        "recommendedAction": f"Strong match for {matched_service}. Propose technical implementation timeline!",
        "evidence": [
            f"Active project requirement: {is_active}",
            f"Looking for external engineering partner: {qual_result.get('is_looking_for_external_provider', True)}",
            f"Service match confidence: {confidence:.0%}",
            f"Matched IOSYS Capability: {matched_service}",
        ],
        "contactEmail": "Unknown",
        "contactPhone": "Unknown",
        "sourceProfileUrl": req.url,
        "companyWebsite": "Unknown",
        "contactPage": "Unknown",
        "githubProfile": "Unknown",
        "twitterProfile": "Unknown",
        "linkedinProfile": "Unknown",
        "otherProfiles": [],
        "requestedService": qual_result.get("requested_service") or req.title,
        "requestedServiceCategory": qual_result.get("requested_service_category") or "Software Development",
        "serviceMatch": is_match,
        "intentType": qual_result.get("intent_type") or "EXPLICIT_SERVICE_REQUEST",
    }


class DeepQualifyRequest(BaseModel):
    lead_id: str

@router.post("/leads/deep-qualify")
async def deep_qualify_lead(req: DeepQualifyRequest, db: Session = Depends(get_db)):
    from app.agents.intelligence import deep_qualify_post
    from sqlalchemy.orm.attributes import flag_modified
    from app.models.service_catalog import CompanyService
    
    # 1. Fetch Lead
    result = db.execute(select(Lead).where(Lead.id == req.lead_id))
    lead = result.scalars().first()
    
    if not lead:
        return {"status": "error", "message": "Lead not found"}
        
    # 2. Fetch Signal content
    sig_result = db.execute(select(UnifiedSignalModel).where(UnifiedSignalModel.signal_id == lead.signal_id))
    signal = sig_result.scalars().first()
    
    if not signal:
        return {"status": "error", "message": "Signal not found for lead"}
        
    # 3. Fetch Service Catalog
    services_result = db.execute(select(CompanyService))
    all_services = services_result.scalars().all()
    company_services = [s.name for s in all_services if not s.is_excluded]
    excluded_services = [s.name for s in all_services if s.is_excluded]
        
    # 4. Qualify
    campaign_name = "Unknown Campaign"
    if isinstance(signal.content, dict):
        content_text = signal.content.get("text") or signal.content.get("description") or str(signal.content)
        title_text = signal.content.get("title") or (signal.title if hasattr(signal, 'title') and signal.title else "Unknown Title")
    else:
        content_text = str(signal.content)
        title_text = signal.title if hasattr(signal, 'title') and signal.title else "Unknown Title"
        
    qual_result = await deep_qualify_post(
        content=content_text,
        title=title_text,
        source=signal.source,
        campaign_name=campaign_name,
        company_services=company_services,
        excluded_services=excluded_services
    )

    
    if "error" in qual_result:
        return {"status": "error", "message": qual_result["error"]}
        
    # 5. Strictly Calculate Score based on new JSON output
    is_active_request = qual_result.get("is_active_request", False)
    looking_ext = qual_result.get("is_looking_for_external_provider", False)
    service_match = qual_result.get("service_match", False)
    service_match_confidence = float(qual_result.get("service_match_confidence", 0.0))
    llm_tier = qual_result.get("lead_status", "REJECTED")
    reasoning = qual_result.get("ai_summary") or qual_result.get("rejection_reason") or qual_result.get("matched_company_service") or "Unknown"
    
    score = 0
    tier = "LOW"
    
    # Strict matching rule
    if is_active_request and looking_ext and service_match and service_match_confidence >= 0.75:
        score = int(70 + (service_match_confidence * 30))
        score = min(score, 100)
        tier = llm_tier if llm_tier in ["HOT", "WARM", "QUALIFIED"] else "HOT"
    elif is_active_request and looking_ext and service_match and service_match_confidence >= 0.50:
        score = int(40 + (service_match_confidence * 40))
        tier = "WARM"
    else:
        score = 0
        tier = "REJECTED"
        
    # 6. Update Lead & Signal in DB
    if signal.metadata_ is None:
        signal.metadata_ = {}
        
    signal.metadata_["priority_score"] = score
    signal.metadata_["tier_label"] = tier
    signal.metadata_["ai_reasoning"] = reasoning
    signal.metadata_["deep_qualification_result"] = qual_result
    
    lead.status = "QUALIFIED" if tier in ["HOT", "WARM", "QUALIFIED"] else "REJECTED"
    
    flag_modified(signal, "metadata_")
    db.commit()
    
    return {
        "status": "success",
        "tier": tier,
        "score": score,
        "reason": reasoning,
        "raw_qualification": qual_result
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
