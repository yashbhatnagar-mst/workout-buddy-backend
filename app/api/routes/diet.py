from fastapi import APIRouter, HTTPException, Depends
from app.core.auth import get_current_user_id
from app.schemas.diet_plan import DietFormRequest
from app.db.mongodb import db
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import re
import json
from app.utils.api_response import api_response
from app.utils.groq import get_groq_response


router = APIRouter(prefix="/diet", tags=["Diet"])

def extract_json_from_text(text: str):
    clean_text = re.sub(r"```json\s*|```", "", text).strip()
    json_match = re.search(r"\{.*\}", clean_text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(0))
    raise ValueError("No valid JSON found in response")

def get_next_dates(n: int):
    today = datetime.now(timezone.utc).date()
    return [(today + timedelta(days=i)).isoformat() for i in range(n)]

@router.post("/generate-diet-plan/")
async def generate_diet_plan(request: DietFormRequest, user_id: str = Depends(get_current_user_id)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user_id")

    number_of_days = request.preferred_training_days_per_week or 7
    days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    selected_days = days_of_week[:min(number_of_days, 7)]

    prompt = f"""
You are a certified dietitian and fitness expert.

Return a {len(selected_days)}-day **diet plan in strict JSON format.**
Each day must include **breakfast, lunch, and dinner.**
Return only the following days: {', '.join(selected_days)}.

Strictly follow this JSON format:
{{
    "monday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "...",
        "calories": "..."
    }},
    "tuesday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "...",
        "calories": "..."
    }},
    "wednesday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "...",
        "calories": "..."
    }},
    "thursday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "...",
        "calories": "..."
    }},
    "friday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "...",
        "calories": "..."
    }},
    "saturday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "...",
        "calories": "..."
    }},
    "sunday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "...",
        "calories": "..."
    }}
}}

User Profile:
- Diet preference: {request.diet_type}
- Activity Level: {request.activity_level}
- Fitness Goal: {request.fitness_goal}
- Experience Level: {request.experience_level}
- Medical Conditions: {request.medical_conditions}
- Allergies: {request.allergies}
- Other Allergy: {request.other_allergy}
- Preferred Workout Style: {request.preferred_workout_style}
- Preferred Training Days per Week: {request.preferred_training_days_per_week}

Only return JSON for the following days: {', '.join(selected_days)}.
"""

    ai_response = get_groq_response(prompt)

    try:
        diet_plan = extract_json_from_text(ai_response)
    except Exception as e:
        return api_response(
            message="AI did not return valid JSON after cleanup",
            status=400,
            data={"error": str(e), "raw_response": ai_response}
        )

    week_dates = get_next_dates(len(selected_days))

    dated_plan = {
        day: {
            "date": date,
            "meals": diet_plan.get(day, {})
        }
        for day, date in zip(selected_days, week_dates)
    }

    await db["diet_plans"].replace_one(
        {"user_id": ObjectId(user_id)},
        {
            "user_id": ObjectId(user_id),
            "user_profile": request.dict(),
            "week_start_date": week_dates[0],
            "week_end_date": week_dates[-1],
            "ai_generated_plan": dated_plan,
            "created_at": datetime.now(timezone.utc)
        },
        upsert=True
    )

    return api_response(
        message="AI Diet Plan generated successfully",
        status=201,
        data={
            "ai_generated_diet_plan": dated_plan
        }
    )



@router.get("/diet-plan/")
async def get_saved_diet_plan(user_id: str = Depends(get_current_user_id)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid plan_id")

    plan = await db["diet_plans"].find_one({"user_id": ObjectId(user_id)})

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan["_id"] = str(plan["_id"])
    if "user_id" in plan:
        plan["user_id"] = str(plan["user_id"])

    return api_response(
        message="Diet plan retrieved successfully",
        status=200,
        data=plan
    )
