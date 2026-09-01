from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    # Raw inputs
    raw_signal: Dict[str, Any]
    
    # Step 1: Qualification
    is_qualified: bool
    qualification_reason: str
    noise_level: str
    
    # Step 2: Company & Source Discovery
    company_name: Optional[str]
    industry: Optional[str]
    region: Optional[str]
    related_signals: List[Dict[str, Any]]
    
    # Step 3: Opportunity Extraction
    business_pain: Optional[str]
    detected_need: Optional[str]
    technology: Optional[str]
    buying_stage: Optional[str]
    service_fit: Optional[str]
    recommended_action: Optional[str]
    evidence: List[str]
    ai_summary: Optional[str]
    
    # Step 4: Contact & Profile Discovery
    contact_confidence: Optional[int]
    contact_verification: Optional[str]
    source_profile_url: Optional[str]
    company_website: Optional[str]
    contact_page: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    github_profile: Optional[str]
    twitter_profile: Optional[str]
    linkedin_profile: Optional[str]
    other_profiles: List[str]
    
    # Output
    intent_score: int
    confidence_score: int
    final_opportunity: Optional[Dict[str, Any]]
    
    # Execution control
    errors: List[str]
