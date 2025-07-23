from pydantic import BaseModel, Field
from typing import List, Optional


class MealItem(BaseModel):
    item_name: str
    quantity: Optional[float] = None
    weight_in_grams: Optional[float] = None


class MealLogRequest(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    breakfast: Optional[List[MealItem]] = None
    lunch: Optional[List[MealItem]] = None
    dinner: Optional[List[MealItem]] = None
