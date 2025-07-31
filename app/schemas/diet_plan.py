from typing import List, Optional
from pydantic import BaseModel, Field


class DietFormRequest(BaseModel):
    diet_type: str
    activity_level: str
    fitness_goal: str
    experience_level: str
    medical_conditions: List[str]
    allergies: List[str]
    other_allergy: str
    preferred_workout_style: str
    preferred_training_days_per_week: int
    



class DietPlanResponse(BaseModel):
    day: str
    breakfast: str
    lunch: str
    dinner: str


class DietPlanListResponse(BaseModel):
    plan: list[DietPlanResponse]
