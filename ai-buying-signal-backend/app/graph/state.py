from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    # Raw inputs
    raw_signal: Dict[str, Any]
    
    # Context (e.g. active Campaign details to match against)
    campaign_context: Optional[Dict[str, Any]]
    
    # Step 1: Intent Detection
    is_buying_signal: bool
    intent_category: Optional[str]
    intent_confidence: Optional[float]
    what_they_are_looking_for: Optional[str]
    problem_detected: Optional[str]
    urgency: Optional[str]
    author_type: Optional[str]
    reason: Optional[str]
    
    # Step 2: Service Matching
    service_match: bool
    service_match_confidence: Optional[float]
    
    # Step 3: Buying Signal Validation
    priority_score: int
    tier_label: str
    
    # Step 4: Identity Resolution
    company_name: Optional[str]
    contact_confidence: Optional[int]
    contact_verification: Optional[str]
    email: Optional[str]
    linkedin_profile: Optional[str]
    
    # AI Summary
    ai_summary: Optional[str]
    
    # Execution control
    errors: List[str]
