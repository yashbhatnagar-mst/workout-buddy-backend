from fastapi import APIRouter
from app.schemas.meal_log_schema import MealLogRequest, MealLogResponse
from app.db.mongodb import db
from bson import ObjectId

router = APIRouter(prefix="/api/progress", tags=["Meal Log"])


@router.post("/log-meal/{user_id}", response_model=MealLogResponse)
async def log_meal(user_id: str, data: MealLogRequest):
    await db["meal_logs"].insert_one({
        "user_id": ObjectId(user_id),
        "date": data.date,
        "meals": {
            "breakfast": data.breakfast,
            "lunch": data.lunch,
            "dinner": data.dinner
        }
    })

    return {
        "message": "Meal log saved successfully.",
        "logged_data": data
    }
