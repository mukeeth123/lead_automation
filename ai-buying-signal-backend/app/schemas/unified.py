from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime, timezone

class SignalContent(BaseModel):
    title: Optional[str] = None
    body: str
    summary: Optional[str] = None
    
class SignalAuthor(BaseModel):
    username: str
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    avatar_url: Optional[HttpUrl] = None

class UnifiedSignal(BaseModel):
    signal_id: UUID = Field(default_factory=uuid4)
    
    source: str
    source_type: str
    
    external_id: str
    external_url: HttpUrl
    
    campaign_id: Optional[UUID] = None
    
    content: SignalContent
    author: Optional[SignalAuthor] = None
    
    published_at: Optional[datetime] = None
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    language: Optional[str] = None
    
    raw_event_id: UUID
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    content_hash: str
