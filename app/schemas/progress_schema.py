from pydantic import BaseModel, Field
from typing import List, Optional

class MealBreakdown(BaseModel):
    meal_type: str
    total_calories: int
    total_proteins: float
    total_carbs: float
    total_fats: float

class AIProgressSummary(BaseModel):
    user: str
    analysis_period: str
    summary: str
    meal_breakdown: List[MealBreakdown]
    adherence: str
    recommendations: List[str]
