from pydantic import BaseModel, ConfigDict
from typing import Optional

class CompanyBase(BaseModel):
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyRead(CompanyBase):
    id: str
    signals_count: int
    highest_intent_score: int
    model_config = ConfigDict(from_attributes=True)
