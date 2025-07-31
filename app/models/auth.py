from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from pydantic import ConfigDict

class User(BaseModel):
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    email: EmailStr
    password_hash: str
    oauth_provider: str
    is_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        ser_json_typed={ObjectId: str},
        from_attributes=True
    )
