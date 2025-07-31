from pydantic import BaseModel, Field
from datetime import datetime, timezone ,date
from typing import Optional
from bson import ObjectId
from pydantic import ConfigDict

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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        ser_json_typed={ObjectId: str},
        from_attributes=True
    )



class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    activity_level: Optional[str] = None
    goal: Optional[str] = None
