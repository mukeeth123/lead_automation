from pydantic import BaseModel
from typing import List, Tuple

class HeuristicResult(BaseModel):
    score: int
    positive_signals: List[str]
    negative_signals: List[str]
    detected_entities: List[str] = []
    detected_intent_patterns: List[str] = []
    should_continue: bool

class HeuristicScorer:
    def __init__(self):
        # 1. Combinatorial Intents & Targets
        self.intents = ["looking for", "need a", "need an", "searching for", "recommend", "who should we", "has anyone worked with", "hire", "hiring", "who do you use", "any suggestions"]
        self.targets = ["it staffing", "tech recruiting", "staffing firm", "recruiter", "recruiting agency", "staff augmentation", "contract-to-hire", "offshore", "nearshore", "rpo", "eor", "software engineers", "developers", "devops", "cybersecurity", "data engineer", "qa engineer", "tech talent", "agency", "freelancer"]
        
        # 2. Warm Signals
        self.projects = ["scaling our engineering", "rapidly expanding", "building our engineering", "new product launch", "raised funding", "mass technical hiring", "doubling engineering"]
        self.pain = ["struggling to hire", "behind roadmap", "losing candidates", "time-to-hire", "sitting open for months", "technical hiring process is broken", "ghost us", "not getting applicants", "can't retain", "interview scheduling is a nightmare", "making bad technical hires"]
        self.tech = ["software", "api", "integration", "app", "cloud", "aws", "azure", "gcp", "react", "node", "python", "kubernetes", "docker", "machine learning", "llm", "sap", "salesforce", "cybersecurity", "network", "devops"]
        self.capacity_gap = ["cto", "vp engineering", "head of data", "chief information officer", "ciso", "engineering leadership", "infrastructure team understaffed", "no internal technical recruiter"]
        
        # 3. Aggressive Negative Sellers & Noise List
        self.sellers = ["i am a", "we are a", "available for", "my freelance", "my agency", "i built", "check out my", "our company provides", "i can help", "let me help", "hire me", "my portfolio", "i am an", "my services", "i offer", "student", "internship", "jobseeker", "looking for a job", "seeking employment", "resume", "apply now", "entry level", "bootcamp", "certification", "how to become"]
        self.non_tech_roles = ["maintenance technician", "landscaping", "nurse", "retail staff", "warehouse", "delivery driver", "plumber", "electrician", "cleaner", "cashier", "cook", "chef", "server", "bartender", "grounds location", "estimator"]
        
        # 4. Explicit Negative Intent (Negations)
        self.negative_intent = ["don't need", "do not need", "not looking for", "already solved", "not interested", "no agencies", "no recruiters", "we have an agency", "already partnered"]

    def analyze(self, text: str, title: str = "") -> HeuristicResult:
        full_text = f"{title} {text}".lower()
        score = 0
        positive_signals = []
        negative_signals = []
        intent_patterns = []
        
        # Negative intent check first
        neg_match = sum(1 for k in self.negative_intent if k in full_text)
        if neg_match > 0:
            return HeuristicResult(
                score=0,
                positive_signals=[],
                negative_signals=["Detected explicit negative intent (e.g. 'not looking for')."],
                should_continue=False
            )
            
        b_match = 0
        if any(i in full_text for i in self.intents) and any(t in full_text for t in self.targets):
            b_match = 2
            
        proj_match = sum(1 for k in self.projects if k in full_text)
        p_match = sum(1 for k in self.pain if k in full_text)
        t_match = sum(1 for k in self.tech if k in full_text)
        c_match = sum(1 for k in self.capacity_gap if k in full_text)
        
        s_match = sum(1 for k in self.sellers if f" {k} " in f" {full_text} " or f" {k}." in f" {full_text}")
        nt_match = sum(1 for k in self.non_tech_roles if k in full_text)
        
        # Scoring Logic
        if s_match or nt_match:
            penalty = min((s_match + nt_match) * 50, 100)
            score -= penalty
            negative_signals.append(f"-{penalty}: Heavy Seller/Noise or Non-Tech Role penalty")
            
        if b_match: 
            pts = 50
            score += pts
            positive_signals.append(f"+{pts}: Direct buying/agency intent")
            intent_patterns.append("Direct Agency Request")
        
        if proj_match:
            pts = min(proj_match * 15, 30)
            score += pts
            positive_signals.append(f"+{pts}: Tech growth/scaling signals")
            intent_patterns.append("Company Scaling")
            
        if p_match: 
            pts = min(p_match * 10, 20)
            score += pts
            positive_signals.append(f"+{pts}: Tech hiring pain points")
            intent_patterns.append("Expressed Pain")
            
        if t_match: 
            pts = min(t_match * 5, 15)
            score += pts
            positive_signals.append(f"+{pts}: Tech context keywords")
            
        if c_match:
            pts = min(c_match * 20, 40)
            score += pts
            positive_signals.append(f"+{pts}: Tech capacity gap / Leadership hiring signal")
            intent_patterns.append("Leadership Gap")
        
        if (b_match or proj_match) and t_match: 
            score += 15
            positive_signals.append("+15: Project + Tech synergy bonus")
            
        if p_match and t_match: 
            score += 10
            positive_signals.append("+10: Pain + Tech master combo")
            
        final_score = max(0, min(score, 100))
        
        # Candidate requires a score >= 40 normally, but we leave the threshold decision to the pipeline.
        should_continue = final_score >= 20 # Lowered initial barrier for LLM qualification
        
        return HeuristicResult(
            score=final_score,
            positive_signals=positive_signals,
            negative_signals=negative_signals,
            detected_intent_patterns=intent_patterns,
            should_continue=should_continue
        )
