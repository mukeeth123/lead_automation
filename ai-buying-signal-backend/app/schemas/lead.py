from pydantic import BaseModel, ConfigDict
from typing import Optional

class LeadBase(BaseModel):
    company_id: str
    status: str = "New"
    contact_email: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadRead(LeadBase):
    id: str
    model_config = ConfigDict(from_attributes=True)
