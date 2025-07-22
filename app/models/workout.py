# app/models/workout.py
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime,timezone
from app.schemas.workout import WorkoutPlanDay

class WorkoutDietPlan(BaseModel):
    user_id: str = Field(..., description="ID of the user this plan belongs to")
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    activity_level: str
    goal: str
    workout_days_per_week: int
    workout_duration: str
    medical_conditions: List[str]
    injuries_or_limitations: List[str]
    plan: List[WorkoutPlanDay] = Field(..., description="The generated 7-day workout plan")
    created_at: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Timestamp of plan creation"
)


    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True # Required for ObjectId
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }
