from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from app.db.mongodb import db
from app.core.auth import get_current_user_id
from app.utils.api_response import api_response

router = APIRouter(prefix="/diet", tags=["Diet"])

@router.delete("/delete-diet-plan/")
async def delete_diet_plan(user_id: str = Depends(get_current_user_id)):
    # Validate ObjectId
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid plan_id")

    # Find the diet plan
    plan = await db["diet_plans"].find_one({"_id": ObjectId(user_id)})

    # If not found
    if not plan:
        raise HTTPException(status_code=404, detail="Diet plan not found")

    # Ensure the user owns the plan
    if str(plan.get("user_id")) != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this diet plan")

    # Delete the plan
    await db["diet_plans"].delete_one({"_id": ObjectId(user_id)})

    return api_response(
        message="Diet plan deleted successfully",
        status=200
    )
