# app/api/routes/ai_progress.py

from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user_id
from app.utils.api_response import api_response
from app.utils.gemini import generate_gemini_response
from app.db.mongodb import db
from bson import ObjectId
from datetime import datetime


router = APIRouter(prefix="/api/progress/ai", tags=["AI Diet Progress"])


@router.get("/generate")
async def generate_ai_progress(
    user_id: str = Depends(get_current_user_id),
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD")
):
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        if start > end:
            raise ValueError
    except ValueError:
        return api_response(message="Invalid date range.", status=400)

    logs_cursor = db["meal_logs"].find({
        "user_id": ObjectId(user_id),
        "date": {"$gte": start_date, "$lte": end_date}
    })

    logs = []
    async for log in logs_cursor:
        logs.append({
            "date": log["date"],
            "breakfast": log["meals"].get("breakfast", []),
            "lunch": log["meals"].get("lunch", []),
            "dinner": log["meals"].get("dinner", [])
        })

    if not logs:
        return api_response(message="No meal logs found in this date range.", status=404)

    # Prepare a detailed prompt for Gemini
    prompt = f"""You are a professional dietitian. Analyze this user's diet log between {start_date} and {end_date} and generate a progress report. Show calories estimation, missing meals analysis, and adherence insights.
    
Here is the data:
{logs}

Provide insights in bullet points with clarity for visualization in graphs or charts, including:
- Total calories trends
- Missed meals count per day
- Days with best adherence
- Overall feedback
"""

    ai_result = await generate_gemini_response(prompt)

    return api_response(
        message="AI-generated diet progress report.",
        status=200,
        data={
            "start_date": start_date,
            "end_date": end_date,
            "ai_generated_summary": ai_result
        }
    )
