from fastapi import APIRouter, Depends, Query, HTTPException
from app.core.auth import get_current_user_id
from app.utils.api_response import api_response
from app.utils.groq import get_groq_response
from app.db.mongodb import db
from bson import ObjectId
from datetime import datetime
import json
from starlette.concurrency import run_in_threadpool

router = APIRouter()
users_profile = db["user_profiles"]

@router.get("/Diet/generate")
async def generate_ai_progress(
    user_id: str = Depends(get_current_user_id),
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD")
):
    print(f"Generating AI diet progress for user {user_id} from {start_date} to {end_date}")

    # Validate dates
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        if start > end:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date range.")

    # Fetch meal logs
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
        raise HTTPException(status_code=404, detail="No meal logs found in this date range.")

    # Fetch user profile
    profile = await users_profile.find_one({"user_id": user_id})
    if not profile or "weight" not in profile:
        raise HTTPException(status_code=404, detail="User profile not found or missing weight info.")

    weight = profile["weight"]

    # Prompt for Groq AI
    prompt = f"""
You are a certified AI dietitian.

Your task is to analyze the user's diet between {start_date} and {end_date} based on their meal logs and weight. The user's weight is {weight} kg.

== USER DATA ==
Meal Logs:
{logs}

== INSTRUCTIONS ==
You must respond with ONE valid JSON object only.

⚠️ Strict Rules:
- DO NOT include markdown (like triple backticks), code blocks, or any explanatory text.
- DO NOT omit or rename any required fields.
- DO NOT add extra fields.
- DO NOT write any introduction or summary outside the JSON.

== REQUIRED JSON FORMAT ==
{{
"dietProgressReport": {{
    "userProfile": {{
        "weight": "{weight} kg",
        "period": "{start_date} to {end_date}"
    }},
    "overviewSummary": ["..."],
    "estimatedCalorieBreakdown": {{
        "notes": "...",
        "dailyAverages": {{
            "breakfast": 0,
            "lunch": 0,
            "dinner": 0,
            "totalDaily": 0
        }},
        "dailyLog": [
            {{
                "date": "YYYY-MM-DD",
                "calories": {{
                    "breakfast": 0,
                    "lunch": 0,
                    "dinner": 0,
                    "total": 0
                }}
            }}
        ],
        "visualizationSuggestion": {{
            "title": "...",
            "charts": [
                {{
                    "type": "...",
                    "description": "..."
                }}
            ]
        }}
    }},
    "mealLoggingConsistency": {{
        "consistencyPercentage": 0.0,
        "summary": "...",
        "missedMeals": "..."
    }},
    "adherenceAnalysis": {{
        "adherencePercentage": 0.0,
        "summary": "...",
        "bestAdherenceDays": "...",
        "consumptionPattern": "..."
    }},
    "insightsAndRecommendations": {{
        "nutritionalFeedback": [
            {{
                "area": "...",
                "points": ["..."]
            }}
        ],
        "recommendations": [
            {{
                "title": "...",
                "suggestions": ["..."]
            }},
            {{
                "title": "...",
                "example": "..."
            }}
        ]
    }},
    "conclusion": "..."
}}
}}

ONLY return this JSON object. NOTHING else.
"""

    try:
        ai_result = await run_in_threadpool(get_groq_response, prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI request failed: {str(e)}")

    def extract_json_from_response(text: str):
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1 or start > end:
            raise ValueError("No valid JSON object found in AI output.")
        json_str = text[start:end+1]
        return json.loads(json_str)

    try:
        data = extract_json_from_response(ai_result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse AI response: {str(e)}")

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
