from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    oauth_provider: str = "local"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    email: EmailStr
    oauth_provider: str
    created_at: datetime

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str

class ResendOTP(BaseModel):
    email:EmailStr