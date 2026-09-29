from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CompanyAnalyzeRequest(BaseModel):
    query: str = Field(..., description="Company name or search query")

class CompanyResponse(BaseModel):
    id: str
    name: str
    website: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    tech_stack: List[str] = []
    
    icp_score: int
    icp_tier: Optional[str] = None
    ai_summary: Optional[str] = None
    key_executives: Optional[str] = None
    company_size: Optional[str] = None
    latest_updates: List[str] = []
    sales_triggers: List[str] = []
    pain_points: List[str] = []
    pitch_recommendations: List[str] = []
    
    created_at: datetime
    
    class Config:
        from_attributes = True

class CompanyListResponse(BaseModel):
    companies: List[CompanyResponse]

class CompanyChatRequest(BaseModel):
    message: str

class CompanyChatResponse(BaseModel):
    reply: str
