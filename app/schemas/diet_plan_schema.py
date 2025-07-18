from pydantic import BaseModel, Field
from typing import Dict, Literal


class DailyMealPlan(BaseModel):
    date: str  # ISO date string 'YYYY-MM-DD'
    meals: Dict[Literal["breakfast", "lunch", "dinner"], str]


class AIGeneratedDietPlan(BaseModel):
    monday: DailyMealPlan
    tuesday: DailyMealPlan
    wednesday: DailyMealPlan
    thursday: DailyMealPlan
    friday: DailyMealPlan
    saturday: DailyMealPlan
    sunday: DailyMealPlan


class DietPlanInDB(BaseModel):
    user_profile: dict
    week_start_date: str  # ISO date 'YYYY-MM-DD'
    week_end_date: str    # ISO date 'YYYY-MM-DD'
    ai_generated_plan: AIGeneratedDietPlan


class DietPlanResponse(BaseModel):
    message: str
    diet_plan_id: str
    ai_generated_diet_plan: AIGeneratedDietPlan


class ErrorResponse(BaseModel):
    error: str
    raw_response: str | None = None
    exception: str | None = None
        