from pydantic import BaseModel, ConfigDict

class SourceBase(BaseModel):
    name: str
    tag: str

class SourceCreate(SourceBase):
    pass

class SourceRead(SourceBase):
    id: str
    model_config = ConfigDict(from_attributes=True)
