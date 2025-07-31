from fastapi import APIRouter, Depends, Query, HTTPException
from app.core.auth import get_current_user_id
from app.utils.api_response import api_response
from app.db.mongodb import db
from bson import ObjectId
from datetime import datetime, timezone
import re
import json
from app.schemas.workout_progress import WorkoutProgressAPIResponse
from app.utils.groq import get_groq_response
from starlette.concurrency import run_in_threadpool

router = APIRouter()
users_profile = db["user_profiles"]
workout_logs = db["workout_completions"]
workout_plans = db["workout_plans"]
progress_collection = db["workout_progress_logs"]


@router.get("/Workout/generate", response_model=WorkoutProgressAPIResponse)
async def generate_ai_workout_progress(
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

    logs_cursor = workout_logs.find({
        "user_id": ObjectId(user_id),
        "date": {"$gte": start_date, "$lte": end_date}
    })

    logs = []
    async for log in logs_cursor:
        exercises = [
            {
                "name": ex["name"],
                "sets": ex["sets"],
                "reps": ex["reps"],
                "equipment": ex["equipment"],
                "completed": ex.get("completed", False)
            }
            for ex in log.get("exercises", [])
        ]
        logs.append({
            "date": log["date"],
            "status": log.get("status", ""),
            "exercises": exercises
        })

    if not logs:
        return api_response(message="No workout logs found in this date range.", status=404)

    profile = await users_profile.find_one({"user_id": user_id})
    if not profile:
        return api_response(message="User profile not found.", status=404)

    latest_plan = await workout_plans.find_one(
        {"user_id": ObjectId(user_id)},
        sort=[("created_at", -1)]
    )

    prompt = f"""
You are a certified fitness coach AI. Based on the user's profile and workout logs between {start_date} and {end_date}, return a minimal progress summary in structured JSON format for tracking and visualization.

== User Profile ==
Name: {profile.get("name", "N/A")}
Age: {profile.get("age", "N/A")}
Gender: {profile.get("gender", "N/A")}
Height: {profile.get("height", "N/A")} cm
Weight: {profile.get("weight", "N/A")} kg
Activity Level: {profile.get("activity_level", "N/A")}
Goal: {profile.get("goal", "N/A")}
Workout Days/Week: {profile.get("workout_days_per_week", "N/A")}
Workout Duration: {profile.get("workout_duration", "N/A")}

== Workout Logs ==
{logs}

== Output Instructions ==
Return only a valid JSON object in the following exact format:

{{
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "completed_days": int,
  "total_days": int,
  "consistency": float *100 "%",
  "average_rpe": float,
  "total_sets": int,
  "total_reps": int,
  "sum_of_all_calorie_burnout": int,
  "dailyLog": [
    {{
      "date": "YYYY-MM-DD",
      "calorie_burnout": int
    }}
  ],
  "muscle_distribution": {{
    "chest": int,
    "legs": int,
    "back": int,
    "arms": int,
    "shoulders": int,
    "core": int,
    "other": int
  }},
  "weight": float,
  "tips": [
    {{
      "title": "string",
      "tips": ["string", "..."]
    }}
  ]
}}

== Notes ==
- All values must be valid types (no strings for numbers).
- Estimate "calories_burned" based on intensity, duration, and user profile.
- "dailyLog" should reflect estimated burnout per day (even if rest day).
- Provide thoughtful, personalized tips.
"""

    try:
        ai_result = await run_in_threadpool(get_groq_response, prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI request failed: {str(e)}")

    def extract_json_from_response(text: str):
        match = re.search(r"{.*}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in AI output.")
        return json.loads(match.group())

    try:
        data = extract_json_from_response(ai_result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse AI response: {str(e)}")

    # ✅ Deduplicate dailyLog by date and recalculate sum
    if "dailyLog" in data and isinstance(data["dailyLog"], list):
        seen_dates = set()
        unique_log = []
        for entry in data["dailyLog"]:
            entry_date = entry.get("date")
            if entry_date and entry_date not in seen_dates:
                seen_dates.add(entry_date)
                unique_log.append(entry)
        data["dailyLog"] = unique_log
        data["sum_of_all_calorie_burnout"] = sum(entry.get("calorie_burnout", 0) for entry in unique_log)

    # ✅ Save to DB (replacing existing progress for that user and date range)
    await progress_collection.replace_one(
        {
            "user_id": ObjectId(user_id),
            "start_date": start_date,
            "end_date": end_date
        },
        {
            "user_id": ObjectId(user_id),
            "start_date": start_date,
            "end_date": end_date,
            "generated_summary": data,
            "generated_at": datetime.now(timezone.utc)
        },
        upsert=True
    )

    return api_response(
        message="AI-generated workout progress report.",
        status=200,
        data={
            "start_date": start_date,
            "end_date": end_date,
            "summary": data
        }
    )
