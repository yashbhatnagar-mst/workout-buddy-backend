from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


class UserProfile(BaseModel):
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    user_id: str
    full_name: str
    age: int
    gender: str
    height: float
    weight: float
    activity_level: str
    goal: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        from_attributes = True


# class UserProfileCreate(BaseModel):
#     full_name: str
#     age: int
#     gender: str
#     height: float
#     weight: float
#     activity_level: str
#     goal: str


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    activity_level: Optional[str] = None
    goal: Optional[str] = None
