from fastapi import APIRouter
from app.schemas.ai_diet_plan_request import WorkoutPlanRequest
from app.schemas.diet_plan_schema import DietPlanResponse, ErrorResponse
from app.utils.gemini import generate_gemini_response
from app.db.mongodb import db
from bson import ObjectId
from datetime import datetime, timedelta
import re
import json

router = APIRouter(prefix="/ai", tags=["AI Diet"])

# ---------- Utility: Clean AI Output ---------- #
def extract_json_from_text(text: str):
    clean_text = re.sub(r"```json\s*|```", "", text).strip()
    json_match = re.search(r"\{.*\}", clean_text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(0))
    raise ValueError("No valid JSON found in response")

# ---------- Utility: Generate Week Dates ---------- #
from datetime import datetime, timedelta

def get_next_seven_days_dates():
    today = datetime.utcnow().date()
    return [(today + timedelta(days=i)).isoformat() for i in range(7)]


# ---------- POST: Generate AI Diet Plan ---------- #
@router.post(
    "/generate-diet-plan/{user_id}",
    response_model=DietPlanResponse,
    responses={400: {"model": ErrorResponse}}
)
async def generate_ai_diet_plan(user_id: str, request: WorkoutPlanRequest):
    # Prompt for Gemini AI
    print("user_id:", user_id)
    from bson import ObjectId
    print("is valid ObjectId:", ObjectId.is_valid(user_id))
    prompt = f"""
You are a certified dietitian and fitness expert.

Return a 7-day **diet plan in strict JSON format.**
Each day must include **breakfast, lunch, and dinner.**
{{
    "monday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "..."
    }},
    "tuesday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "..."
    }},
    "wednesday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "..."
    }},
    "thursday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "..."
    }},
    "friday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "..."
    }},
    "saturday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "..."
    }},
    "sunday": {{
        "breakfast": "...",
        "lunch": "...",
        "dinner": "..."
    }}
}}


User Profile:
- Diet preference: {request.veg_or_non_veg}
- Activity Level: {request.activity_level}
- Fitness Goal: {request.fitness_goal}
- Experience Level: {request.experience_level}
- Medical Conditions: {request.medical_conditions}
- Allergies: {request.allergies}
- Preferred Workout Style: {request.preferred_workout_style}
- Preferred Training Days per Week: {request.preferred_training_days_per_week}

Output must strictly be JSON for all 7 days.
"""

    # Generate AI Response
    ai_response = await generate_gemini_response(prompt)

    # Clean + Parse Response
    try:
        diet_plan = extract_json_from_text(ai_response)
    except Exception as e:
        return {
            "error": "AI did not return valid JSON after cleanup",
            "raw_response": ai_response,
            "exception": str(e)
        }

    # Add Dates to Each Day
    week_dates = get_next_seven_days_dates()
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


    dated_plan = {
    day: {
        "date": date,
        "meals": diet_plan.get(day, {})
    }
    for day, date in zip(days, week_dates)
}

    # Save to DB
    
    result = await db["diet_plans"].insert_one({
        "user_id": ObjectId(user_id),
        "user_profile": request.dict(),
        "week_start_date": week_dates[0],
        "week_end_date": week_dates[-1],
        "ai_generated_plan": dated_plan,
        "created_at": datetime.utcnow()
    })

    return {
        "message": "Diet plan saved successfully.",
        "diet_plan_id": str(result.inserted_id),
        "ai_generated_diet_plan": dated_plan
    }

# ---------- GET: Retrieve Saved Diet Plan ---------- #
from bson import ObjectId
from fastapi import HTTPException

from bson import ObjectId
from fastapi import HTTPException

@router.get("/diet-plan/{plan_id}")
async def get_saved_diet_plan(plan_id: str):
    plan = await db["diet_plans"].find_one({"_id": ObjectId(plan_id)})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Convert ObjectId fields to string
    plan["_id"] = str(plan["_id"])
    if "user_id" in plan:
        plan["user_id"] = str(plan["user_id"])
    return plan


