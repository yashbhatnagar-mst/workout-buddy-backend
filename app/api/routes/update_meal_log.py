from fastapi import APIRouter, Depends, HTTPException
from app.schemas.meal_log import MealLogRequest
from app.db.mongodb import db
from bson import ObjectId
from datetime import datetime
from app.utils.api_response import api_response
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/meal-log", tags=["Meal Log"])


@router.put("/")
async def update_meal_log(
    data: MealLogRequest,
    user_id: str = Depends(get_current_user_id)
):
    try:
        datetime.fromisoformat(data.date)
    except ValueError:
        return api_response(message="Invalid date format.", status=400)

    existing_log = await db["meal_logs"].find_one({
        "user_id": ObjectId(user_id),
        "date": data.date
    })

    # Merge without duplicates (based on item_name)
    def merge_meals(existing, new):
        if not new:
            return existing
        existing_map = {item["item_name"]: item for item in existing}
        for item in new:
            item_dict = item.dict()
            existing_map[item_dict["item_name"]] = item_dict  # add or update
        return list(existing_map.values())

    if existing_log:
        updated_meals = {
            "breakfast": merge_meals(existing_log["meals"].get("breakfast", []), data.breakfast),
            "lunch": merge_meals(existing_log["meals"].get("lunch", []), data.lunch),
            "dinner": merge_meals(existing_log["meals"].get("dinner", []), data.dinner),
        }

        await db["meal_logs"].update_one(
            {"_id": existing_log["_id"]},
            {"$set": {"meals": updated_meals}}
        )
    else:
        # If no log exists, create a new one
        updated_meals = {
            "breakfast": [item.dict() for item in data.breakfast],
            "lunch": [item.dict() for item in data.lunch],
            "dinner": [item.dict() for item in data.dinner],
        }

        await db["meal_logs"].insert_one({
            "user_id": ObjectId(user_id),
            "date": data.date,
            "meals": updated_meals
        })

    return api_response(
        message="Meal log updated successfully.",
        status=200,
        data={
            "date": data.date,
            "breakfast": updated_meals["breakfast"],
            "lunch": updated_meals["lunch"],
            "dinner": updated_meals["dinner"]
        }
    )
