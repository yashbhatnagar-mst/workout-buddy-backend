from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from app.core.auth import get_current_user_id
from app.db.mongodb import db
from app.utils.api_response import api_response
from app.utils.gemini import generate_gemini_response  # Your Gemini wrapper
from bson import ObjectId

router = APIRouter()

@router.get("/workout/generate")
async def generate_workout_progress_report(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    user_id: str = Depends(get_current_user_id)
):
    try:
        # Parse the dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # Validate user_id
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user_id")

        # Fetch workout logs for date range
        logs_cursor = db.workout_logs.find({
            "user_id": user_id,
            "date": {"$gte": start_date, "$lte": end_date}
        })
        logs = await logs_cursor.to_list(length=None)

        if not logs:
            raise HTTPException(status_code=404, detail="No workout logs found for this date range.")

        # Fetch user profile
        profile = await db.user_profiles.find_one({"user_id": user_id})
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found.")

        # Build prompt for AI
        ai_prompt = {
            "profile": {
                "full_name": profile["full_name"],
                "age": profile["age"],
                "gender": profile["gender"],
                "height": profile["height"],
                "weight": profile["weight"],
                "activity_level": profile["activity_level"],
                "goal": profile["goal"]
            },
            "workout_logs": logs,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "objective": "Generate a complete workout progress report. Include consistency, strength improvements, calories burned, RPE trends, recovery suggestions, and personalized tips based on user's goal and activity."
        }

        # Call Gemini AI
        ai_response = await generate_gemini_response(ai_prompt)

        # Return response
        return api_response(
            message="AI-generated workout progress report.",
            status=200,
            success=True,
            data={
                "start_date": start_date,
                "end_date": end_date,
                "ai_generated_summary": ai_response
            }
        )

    except Exception as e:
        return api_response(
            message=f"Error generating progress report: {str(e)}",
            status=500,
            success=False
        )
    