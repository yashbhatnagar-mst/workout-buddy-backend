from pydantic import BaseModel
from typing import Optional


class MealLogRequest(BaseModel):
    user_id: str  # MongoDB user id
    date: str     # ISO Date: "2025-07-18"
    breakfast: Optional[str] = None
    lunch: Optional[str] = None
    dinner: Optional[str] = None


class MealLogResponse(BaseModel):
    message: str
    logged_data: MealLogRequest
