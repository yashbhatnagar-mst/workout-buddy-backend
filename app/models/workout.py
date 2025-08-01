# app/models/workout.py
from pydantic import BaseModel, Field
from datetime import datetime,timezone , date
from app.schemas.workout import WorkoutPlanDay
from typing import List, Optional, Literal
from bson import ObjectId
from pydantic import ConfigDict

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




class ExerciseLogModel(BaseModel):
    name: str
    sets: int
    reps: str
    weight: Optional[float]
    rest_time_sec: Optional[int]
    rpe: Optional[int]

class WorkoutDayLogModel(BaseModel):
    user_id: ObjectId
    plan_id: ObjectId
    date: date
    status: Literal["completed", "skipped"]
    logged_at: datetime
    exercises: Optional[List[ExerciseLogModel]] = None

    model_config = ConfigDict(
        validate_by_name=True,
        arbitrary_types_allowed=True,
        ser_json_typed={datetime: lambda dt: dt.isoformat()}
    )
