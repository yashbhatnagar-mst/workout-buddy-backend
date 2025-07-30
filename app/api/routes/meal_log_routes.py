from fastapi import APIRouter, Depends
from app.schemas.meal_log import MealLogRequest
from app.db.mongodb import db
from bson import ObjectId
from datetime import datetime
from app.utils.api_response import api_response
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/meal-log", tags=["Meal Log"])


@router.post("/")
async def log_meal(
    data: MealLogRequest,
    user_id: str = Depends(get_current_user_id)
):
    # Validate date format
    try:
        datetime.fromisoformat(data.date)
    except ValueError:
        return api_response(message="Invalid date format.", status=400)
    print("=== Incoming Meal Log ===")
    print("Date:", data.date)
    print("Breakfast:", data.breakfast)
    print("Lunch:", data.lunch)
    print("Dinner:", data.dinner)

# Optional: inspect as dict
    print("Breakfast (dict):", [item.dict() for item in data.breakfast])


    # Convert Pydantic MealItem objects to dicts
    breakfast_items = [item.dict() for item in data.breakfast]
    lunch_items = [item.dict() for item in data.lunch]
    dinner_items = [item.dict() for item in data.dinner]

    # Upsert the meal log
    await db["meal_logs"].update_one(
        {"user_id": ObjectId(user_id), "date": data.date},
        {
            "$set": {
                "user_id": ObjectId(user_id),
                "date": data.date,
                "meals": {
                    "breakfast": breakfast_items,
                    "lunch": lunch_items,
                    "dinner": dinner_items
                }
            }
        },
        upsert=True
    )

    return api_response(
        message="Meal log saved successfully (updated if existed).",
        status=201,
        data={
            "date": data.date,
            "breakfast": breakfast_items,
            "lunch": lunch_items,
            "dinner": dinner_items
        }
    )
