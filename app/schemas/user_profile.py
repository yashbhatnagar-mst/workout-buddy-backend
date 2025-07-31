from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
from bson import ObjectId
from pydantic import ConfigDict


class UserProfileCreate(BaseModel):
    full_name: str = Field(..., description="Full name of the user")
    age: int = Field(..., description="Age of the user")
    gender: Literal["male", "female", "other"] = Field(..., description="Gender of the user")
    height: float = Field(..., description="Height in centimeters")
    weight: float = Field(..., description="Weight in kilograms")
    activity_level: Literal[
        "sedentary", "light", "moderate", "active", "very_active"
    ] = Field(..., description="Physical activity level of the user")
    goal: Literal[
        "lose_weight", "gain_muscle", "maintain_fitness"
    ] = Field(..., description="Fitness goal of the user")
 

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, description="Full name of the user")
    age: Optional[int] = Field(None, description="Age of the user")
    gender: Optional[Literal["male", "female", "other"]] = Field(None, description="Gender of the user")
    height: Optional[float] = Field(None, description="Height in centimeters")
    weight: Optional[float] = Field(None, description="Weight in kilograms")
    activity_level: Optional[str] = Field(None, description="Physical activity level of the user")
    goal: Optional[str] = Field(None, description="Fitness goal of the user")


class UserProfileOut(BaseModel):
    id: str = Field(..., alias="_id", description="Profile ID")
    user_id: str = Field(..., description="Reference ID to the user")
    full_name: str = Field(..., description="Full name of the user")
    age: int = Field(..., description="Age of the user")
    gender: str = Field(..., description="Gender of the user")
    height: float = Field(..., description="Height in centimeters")
    weight: float = Field(..., description="Weight in kilograms")
    activity_level: str = Field(..., description="Physical activity level of the user")
    goal: str = Field(..., description="Fitness goal of the user")
    created_at: datetime = Field(..., description="Profile creation timestamp")

    model_config = ConfigDict(
        validate_by_name=True,
        arbitrary_types_allowed=True,
        ser_json_typed={ObjectId: str}
    )
