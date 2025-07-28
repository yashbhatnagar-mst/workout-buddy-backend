# app/api/routes/ai_progress.py
from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user_id
from app.utils.api_response import api_response
from app.utils.gemini import generate_gemini_response
from app.db.mongodb import db
from bson import ObjectId
from datetime import datetime
import re
import json

router = APIRouter()
users_profile = db["user_profiles"]
workout_logs = db["workout_logs"]

@router.get("/Workout/generate")
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

    profile = await users_profile.find_one({"user_id": ObjectId(user_id)})
    if not profile:
        return api_response(message="User profile not found.", status=404)

    prompt = f"""
You are a certified fitness coach AI. Analyze the user's workout performance between {start_date} and {end_date} based on their logs and profile.

== User Profile ==
Name: {profile.get("name", "N/A")}
Age: {profile.get("age", "N/A")}
Gender: {profile.get("gender", "N/A")}
Height: {profile.get("height_cm", "N/A")} cm
Weight: {profile.get("weight_kg", "N/A")} kg
Activity Level: {profile.get("activity_level", "N/A")}
Goal: {profile.get("goal", "N/A")}
Workout Days/Week: {profile.get("workout_days_per_week", "N/A")}
Workout Duration: {profile.get("workout_duration", "N/A")}

== Workout Logs ==
{logs}

== Output Instructions ==
- Output ONLY a valid JSON object (NO markdown, NO explanation, NO code blocks, NO comments).
- The response must follow this exact structure:

{{
  "workoutProgressReport": {{
    "userProfile": {{
      "weight": "string (e.g., '70.0 kg')",
      "period": "string (e.g., '2025-07-01 to 2025-07-28')"
    }},
    "overviewSummary": ["string", "..."],
    "consistencyAnalysis": {{
      "completedDays": int,
      "totalDays": int,
      "consistencyPercentage": float,
      "summary": "string"
    }},
    "intensityAndVolumeTrends": {{
      "averageRPE": float,
      "totalSets": int,
      "totalReps": int,
      "weightLiftedSummary": "string"
    }},
    "muscleGroupFocus": {{
      "muscleGroupDistribution": {{
        "chest": int,
        "legs": int,
        "back": int,
        "arms": int,
        "shoulders": int,
        "core": int,
        "other": int
      }},
      "summary": "string"
    }},
    "insightsAndRecommendations": {{
      "trainingFeedback": [
        {{
          "area": "string (e.g., 'Positives' or 'Needs Improvement')",
          "points": ["string", "..."]
        }}
      ],
      "suggestions": [
        {{
          "title": "string",
          "tips": ["string", "..."]
        }}
      ]
    }},
    "conclusion": "string"
  }}
}}

== Notes ==
- Do NOT include any markdown or extra wrapping.
- Return a clean JSON response with no missing fields.
"""

    ai_result = await generate_gemini_response(prompt)
    cleaned = re.sub(r'^```(?:json)?\n|\n```$', '', ai_result.strip())
    data = json.loads(cleaned)

    await db["workout_progress_logs"].insert_one({
        "user_id": ObjectId(user_id),
        "start_date": start_date,
        "end_date": end_date,
        "generated_summary": data,
        "generated_at": datetime.utcnow()
    })

    return api_response(
        message="AI-generated workout progress report.",
        status=200,
        data={
            "start_date": start_date,
            "end_date": end_date,
            "summary": data
        }
    )
