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

router = APIRouter(prefix="/api/progress/ai")
users_profile = db["user_profiles"]

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

    profile = await users_profile.find_one({"user_id": user_id})
    if not profile or "weight" not in profile:
        return api_response(message="User profile not found or missing weight info.", status=404)

    weight = profile["weight"]

    prompt = f"""
    You are a certified AI dietitian. Analyze the user's diet between {start_date} and {end_date} based on their meal logs and weight. The user's weight is {weight} kg.

    == Meal Logs ==
    {logs}

    == Output Instructions ==
    - Output ONLY a valid JSON object (NO markdown, NO explanation, NO code blocks, NO comments).
    - The response must match this exact structure:

    {{
    "dietProgressReport": {{
        "userProfile": {{
        "weight": "string (e.g., '58.0 kg')",
        "period": "string (e.g., '2025-07-01 to 2025-07-15')"
        }},
        "overviewSummary": ["string", "..."],
        "estimatedCalorieBreakdown": {{
        "notes": "string",
        "dailyAverages": {{
            "breakfast": int,
            "lunch": int,
            "dinner": int,
            "totalDaily": int
        }},
        "dailyLog": [
            {{
            "date": "YYYY-MM-DD",
            "calories": {{
                "breakfast": int,
                "lunch": int,
                "dinner": int,
                "total": int
            }}
            }}
        ],
        "visualizationSuggestion": {{
            "title": "string",
            "charts": [
            {{
                "type": "string (e.g., 'Bar Chart')",
                "description": "string"
            }}
            ]
        }}
        }},
        "mealLoggingConsistency": {{
        "consistencyPercentage": float,
        "summary": "string",
        "missedMeals": "string"
        }},
        "adherenceAnalysis": {{
        "adherencePercentage": float,
        "summary": "string",
        "bestAdherenceDays": "string",
        "consumptionPattern": "string"
        }},
        "insightsAndRecommendations": {{
        "nutritionalFeedback": [
            {{
            "area": "string (e.g., 'Positives' or 'Areas for Improvement')",
            "points": ["string", "..."]
            }}
        ],
        "recommendations": [
            {{
            "title": "string",
            "suggestions": ["string", "..."]
            }},
            {{
            "title": "string",
            "example": "string"
            }}
        ]
        }},
        "conclusion": "string"
    }}
    }}

    == Important Notes ==
    - Do NOT include markdown (```) or any wrapper.
    - Do NOT include any introductory or explanatory text.
    - Do NOT omit any required fields.
    - Return STRICTLY one JSON object matching the schema above.
    """


    ai_result = await generate_gemini_response(prompt)
            
    cleaned = re.sub(r'^```(?:json)?\n|\n```$', '', ai_result.strip())

    # Load the full response JSON
    data = json.loads(cleaned)

    await db["diet_progress_logs"].insert_one({
        "user_id": ObjectId(user_id),
        "start_date": start_date,
        "end_date": end_date,
        "generated_summary": data,
        "generated_at": datetime.utcnow()
    })

    return api_response(
        message="AI-generated diet progress report.",
        status=200,
        data={
            "start_date": start_date,
            "end_date": end_date,
            "summary": data
        }
    )
