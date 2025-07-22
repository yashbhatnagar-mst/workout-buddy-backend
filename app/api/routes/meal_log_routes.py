from fastapi import APIRouter
from fastapi import Depends
from app.core.auth import get_current_user_id
from app.schemas.meal_log_schema import MealLogRequest
from app.db.mongodb import db
from bson import ObjectId
from datetime import datetime
from app.utils.api_response import api_response


router = APIRouter(prefix="/api/progress", tags=["Meal Log"])


@router.post("/log-meal/{user_id}")
async def log_meal( data: MealLogRequest , user_id: str = Depends(get_current_user_id)):
    # Validate date
    try:
        datetime.fromisoformat(data.date)
    except ValueError:
        return api_response(message="Invalid date format.", status=400, success=False, data=None)

    # Prevent duplicate logs for same user & date
    existing_log = await db["meal_logs"].find_one({
        "user_id": ObjectId(user_id),
        "date": data.date
    })

    if existing_log:
        return api_response(
            message=f"Meal log already exists for {data.date}.",
            status=409,
            success=False,
            data=None
        )

    # Insert new meal log
    await db["meal_logs"].insert_one({
        "user_id": ObjectId(user_id),
        "date": data.date,
        "meals": {
            "breakfast": data.breakfast,
            "lunch": data.lunch,
            "dinner": data.dinner
        }
    })

    return api_response(
        message="Meal log saved successfully.",
        status=201,
        data={
            "user_id": user_id,
            "date": data.date,
            "breakfast": data.breakfast,
            "lunch": data.lunch,
            "dinner": data.dinner
        }
    )
