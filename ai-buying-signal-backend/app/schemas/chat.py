from pydantic import BaseModel

class CompanyChatRequest(BaseModel):
    message: str

