from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any

class RawSignalBase(BaseModel):
    source: str
    external_id: str
    title: Optional[str] = None
    content: str
    author: Optional[str] = None
    author_url: Optional[str] = None
    url: Optional[str] = None
    published_at: datetime
    metadata_: Optional[dict[str, Any]] = None

class RawSignalCreate(RawSignalBase):
    pass

class RawSignalRead(RawSignalBase):
    id: str
    collected_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SignalBase(BaseModel):
    source: str
    source_signal_id: str
    title: Optional[str] = None
    content: str
    url: Optional[str] = None
    author: Optional[str] = None
    published_at: datetime
    
    signal_type: Optional[str] = None
    business_pain: Optional[str] = None
    technology: Optional[str] = None
    detected_need: Optional[str] = None
    explicit_requirement: bool = False
    intent_score: int = 0
    confidence: Optional[float] = None
    ai_summary: Optional[str] = None
    
    company_id: Optional[str] = None
    company: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    iosys_service: Optional[str] = None
    status: str = "New"

class SignalCreate(SignalBase):
    pass

class SignalRead(SignalBase):
    id: str
    collected_at: datetime
    model_config = ConfigDict(from_attributes=True)
