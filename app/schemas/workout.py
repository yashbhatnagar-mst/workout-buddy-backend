# app/schemas/workout.py
from pydantic import BaseModel, Field
from typing import List, Optional

class Exercise(BaseModel):
    name: str = Field(..., description="Name of the exercise")
    sets: int = Field(..., description="Number of sets")
    reps: str = Field(..., description="Number of reps (e.g., '12' or '30 sec')")
    equipment: str = Field(..., description="Equipment required (e.g., 'Dumbbells', 'Bodyweight')")
    duration_per_set: Optional[str] = Field(None, description="Duration for each set (if applicable)")

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
    workout_days_per_week: int = Field(..., ge=0, le=7, description="Number of days per week the user wants to workout")
    workout_duration: str = Field(..., description="Desired workout duration (e.g., '1 hour', '30 minutes')")
    medical_conditions: List[str] = Field(default_factory=list, description="Any medical conditions")
    injuries_or_limitations: List[str] = Field(default_factory=list, description="Any injuries or limitations")

