from pydantic import BaseModel, Field
from typing import List


class DailyProgress(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    total_calories: int
    target_calories: int
    adherence_percent: float
    missed_meals_count: int


class WeeklyProgressResponse(BaseModel):
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    total_calories: int
    target_calories: int
    average_adherence: float
    missed_meals: int
    daily_breakdown: List[DailyProgress]


class MonthlyProgressResponse(BaseModel):
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    total_calories: int
    target_calories: int
    average_adherence: float
    missed_meals: int
    daily_breakdown: List[DailyProgress]
