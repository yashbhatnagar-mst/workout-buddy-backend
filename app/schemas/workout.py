# app/schemas/workout.py
from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime, date



class Exercise(BaseModel):
    name: str = Field(..., description="Name of the exercise")
    sets: int = Field(..., description="Number of sets")
    reps: str = Field(..., description="Number of reps (e.g., '12', '30 sec', 'Max')")
    equipment: str = Field(..., description="Equipment required (e.g., 'Dumbbells', 'Bodyweight')")
    duration_per_set: Optional[str] = Field(None, description="Duration for each set (if applicable)")
    instructions: Optional[List[str]] = Field(
        default=None,
        description="List of tips or guidelines for the exercise"
    )

class WorkoutPlanDay(BaseModel):
    day: str = Field(..., description="Day of the week (e.g., 'Monday')")
    focus: str = Field(..., description="Muscle group or type of training (e.g., 'Chest', 'Cardio', 'Rest')")
    exercises: List[Exercise] = Field(..., description="List of exercises for the day")

class WorkoutDietPlanRequest(BaseModel):
    age: int = Field(..., gt=0, description="User's age")
    gender: str = Field(..., description="User's gender (e.g., 'Male', 'Female', 'Other')")
    height_cm: float = Field(..., gt=0, description="User's height in centimeters")
    weight_kg: float = Field(..., gt=0, description="User's weight in kilograms")
    activity_level: str = Field(..., description="User's activity level (e.g., 'Sedentary', 'Moderately Active')")
    goal: str = Field(..., description="User's fitness goal (e.g., 'Weight Loss', 'Muscle Gain')")
    workout_days_per_week: Optional[int] = Field(3, ge=0, le=7, description="Days per week the user wants to workout")
    workout_duration: Optional[str] = Field("30 minutes", description="Desired workout duration")
    medical_conditions: List[str] = Field(default_factory=list, description="Any medical conditions")
    injuries_or_limitations: List[str] = Field(default_factory=list, description="Any injuries or limitations")


class ExerciseCompletionInput(BaseModel):
    name: str
    sets: Optional[int] = None
    reps: Optional[str] = None
    duration_per_set: Optional[str] = None
    completed: bool

class WorkoutDayLogRequest(BaseModel):
    plan_id: str
    date: date
    status: str  # "completed" or "skipped"
    created_at: Optional[datetime] = None
    exercises: Optional[List[ExerciseCompletionInput]] = None