from pydantic import BaseModel
from datetime import datetime

class ApiKeyCreate(BaseModel):
    apiKey: str
    secret: str

class ApiKeyOut(BaseModel):
    _id: str
    apiKey: str
    active: bool
    createdAt: datetime
