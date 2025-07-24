from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import db
from bson import ObjectId
from app.utils.api_response import api_response
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/meal-log", tags=["Meal Log"])

@router.delete("/")
async def delete_meal_log(
    date: str,
    user_id: str = Depends(get_current_user_id)
):
    result = await db["meal_logs"].delete_one({
        "user_id": ObjectId(user_id),
        "date": date
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Meal log not found")

    return api_response(
        message="Meal log deleted successfully.",
        status=200,
        data={"date": date}
    )
