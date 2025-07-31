from pydantic import BaseModel
from typing import List

class DailyTotalEntry(BaseModel):
    date: str
    total: int

class DietChartResponse(BaseModel):
    period: str
    weight: str
    consistency_percentage: float
    adherence_percentage: float
    daily_chart_data: List[DailyTotalEntry]
