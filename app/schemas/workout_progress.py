from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class Tip(BaseModel):
    title: str
    tips: List[str]

class MuscleDistribution(BaseModel):
    chest: int
    legs: int
    back: int
    arms: int
    shoulders: int
    core: int
    other: int

class DailyBurnout(BaseModel):
    date: str  # or use date if you want strict format validation
    calorie_burnout: int

class WorkoutProgressSummary(BaseModel):
    start_date: str
    end_date: str
    completed_days: int
    total_days: int
    consistency: float
    average_rpe: float
    total_sets: int
    total_reps: int
    dailyLog: List[DailyBurnout]
    sum_of_all_calorie_burnout: int
    muscle_distribution: MuscleDistribution
    weight: float
    tips: List[Tip]

class WorkoutProgressResponse(BaseModel):
    start_date: str
    end_date: str
    summary: WorkoutProgressSummary

class WorkoutProgressAPIResponse(BaseModel):
    message: str
    status: int
    success: bool
    data: WorkoutProgressResponse
