from pydantic import BaseModel
from typing import List


class DailyProgress(BaseModel):
    date: str
    total_calories: int
    target_calories: int
    adherence_percent: float
    missed_meals_count: int


class WeeklyProgressResponse(BaseModel):
    week_start_date: str
    week_end_date: str
    total_calories: int
    target_calories: int
    average_adherence: float
    missed_meals: int
    daily_breakdown: List[DailyProgress]


class MonthlyProgressResponse(BaseModel):
    month: str  # e.g., "July 2025"
    total_calories: int
    target_calories: int
    average_adherence: float
    missed_meals: int
    daily_breakdown: List[DailyProgress]
