import logging
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

def heuristic_score(text: str) -> tuple[int, list[str]]:
    text = text.lower()
    score = 0
    breakdown = []
    
    buying = [
        "looking for a software development agency", "need a software development company",
        "looking for a development partner", "need a technology partner", "need a technical team",
        "looking for an implementation partner", "need an ai development company",
        "looking for an ai automation partner", "searching for a custom software vendor",
        "need a crm implementation partner", "looking for a systems integrator",
        "need an mvp built", "outsourced dev team", "looking for api integration experts",
        "need cloud migration experts", "recommend a good software agency",
        "who should we work with", "has anyone worked with a good dev shop",
        "looking for someone trustworthy to build", "need help finding a technical co-founder"
    ]
    
    projects = [
        "building a new platform", "need to automate our operations",
        "looking to modernize our systems", "migrating from legacy software",
        "building our mvp", "automating our onboarding",
        "migrating to the cloud", "scaling our current platform",
        "replacing our manual spreadsheets", "digital transformation initiative"
    ]
    
    pain = [
        "still doing this manually", "too much manual work", "rely heavily on spreadsheets",
        "manual data entry", "everything is done by hand",
        "workflows are broken", "too many manual steps", "systems are disconnected",
        "nothing talks to each other", "tools don't integrate",
        "data is scattered", "manual reporting takes too long", "can't scale"
    ]
    
    tech = [
        "ai", "automation", "api", "integration", "software", "app", 
        "crm", "erp", "dashboard", "portal", "cloud", "data warehouse",
        "legacy system", "salesforce", "hubspot"
    ]
    
    capacity_gap = [
        "head of engineering", "vp engineering", "cto ", "chief technology officer",
        "build our platform from scratch", "replace our legacy system",
        "scaling engineering headcount", "hiring multiple technical roles"
    ]
    
    b_match = sum(1 for k in buying if k in text)
    proj_match = sum(1 for k in projects if k in text)
    p_match = sum(1 for k in pain if k in text)
    t_match = sum(1 for k in tech if k in text)
    c_match = sum(1 for k in capacity_gap if k in text)
    
    if b_match: 
        score += min(b_match * 25, 50)
    if proj_match:
        score += min(proj_match * 15, 30)
    if p_match: 
        score += min(p_match * 10, 20)
    if t_match: 
        score += min(t_match * 5, 15)
    if c_match:
        score += min(c_match * 20, 40)
    if (b_match or proj_match) and t_match: 
        score += 15
    if p_match and t_match: 
        score += 10
        
    noise = ["job", "hiring", "career", "tutorial", "course", "freelancer", "upwork"]
    n_match = sum(1 for k in noise if f" {k} " in f" {text} ")
    if n_match and not c_match:
        score -= min(n_match * 20, 40)
        
    return max(0, min(score, 100)), breakdown

async def classify_node(state: AgentState) -> AgentState:
    raw = state.get("raw_signal", {})
    text = f"{raw.get('title', '')} {raw.get('clean_content', '')}"
    
    score, _ = heuristic_score(text)
    
    is_qual = score >= 20
    state["is_qualified"] = is_qual
    state["qualification_reason"] = f"Heuristic score is {score}"
    state["noise_level"] = "Low" if score > 50 else "Medium" if score > 20 else "High"
    
    logger.info(f"Node [Classify]: Score {score} -> Qualified: {is_qual}")
    return state
