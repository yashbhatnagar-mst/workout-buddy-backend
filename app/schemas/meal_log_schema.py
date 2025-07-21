from pydantic import BaseModel , Field
from typing import Optional


class MealLogRequest(BaseModel):
    user_id: str  # MongoDB user id
    date: str = Field(..., description="ISO Date: YYYY-MM-DD")
    breakfast: Optional[str] = None
    lunch: Optional[str] = None
    dinner: Optional[str] = None


class MealLogResponse(BaseModel):
    message: str
    logged_data: MealLogRequest
