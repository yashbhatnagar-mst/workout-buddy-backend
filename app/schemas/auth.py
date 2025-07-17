from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
