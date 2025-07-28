from fastapi import APIRouter, Depends
from bson import ObjectId
import json
import re
from app.core.auth import get_current_user_id
from app.db.mongodb import db
from app.utils.gemini import generate_gemini_response
from app.utils.api_response import api_response
from app.schemas.workout import WorkoutDietPlanRequest, WorkoutPlanDay , WorkoutDayLogRequest
from app.models.workout import WorkoutDietPlan
from datetime import datetime, timezone , time , timedelta ,date


router = APIRouter(dependencies=[Depends(get_current_user_id)])
workout_collection = db["workout_plans"]
workout_log_collection = db["workout_completions"]

# 🔧 Prompt builder
def build_workout_prompt(data: WorkoutDietPlanRequest) -> str:
    return (
        f"You are a certified physiotherapist and fitness trainer specializing in injury recovery and adaptive workouts. Generate a safe, effective, and detailed 7-day personalized workout plan (prefer rest on Saturday and Sunday if days are less then 7) in valid JSON format "
        f"for a user with the following profile:\n"
        f"- Age: {data.age}\n"
        f"- Gender: {data.gender}\n"
        f"- Height: {data.height_cm} cm\n"
        f"- Weight: {data.weight_kg} kg\n"
        f"- Activity Level: {data.activity_level}\n"
        f"- Goal: {data.goal}\n"
        f"- Workout Days per Week: {data.workout_days_per_week}\n"
        f"- Workout Duration: {data.workout_duration}\n"
        f"- Medical Conditions: {', '.join(data.medical_conditions) if data.medical_conditions else 'None'}\n"
        f"- Injuries or Limitations: {', '.join(data.injuries_or_limitations) if data.injuries_or_limitations else 'None'}\n\n"

        f"Important Notes:\n"
        f"- If the user has **serious injuries** (e.g., broken leg, spinal issues, missing limb), the plan MUST be designed to avoid strain on the affected areas.\n"
        f"- Use adaptive, low-impact, or seated/rehab exercises as needed.\n"
        f"- Clearly avoid exercises that can aggravate the injuries or limitations.\n"
        f"- Ensure proper form and safety is emphasized in all instructions.\n"
        f"- If needed, rest or recovery days should be included.\n"

        f"Output Instructions:\n"
        f"- Output ONLY a valid JSON array (no markdown, no explanation, no comments).\n"
        f"- The array must contain exactly 7 objects, one for each day of the week (Monday to Sunday).\n"
        f"- Each object must contain:\n"
        f"  - 'day': A string for the day name (e.g., 'Monday')\n"
        f"  - 'focus': A string describing the workout focus (e.g., 'Upper Body Mobility', 'Recovery')\n"
        f"  - 'exercises': A list of exercises (empty list if it's a rest day)\n"
        f"- Each exercise must include:\n"
        f"  - 'name': string (e.g., 'Seated Arm Circles')\n"
        f"  - 'sets': integer (e.g., 2)\n"
        f"  - 'reps': string (e.g., '10-12', '30 seconds', or 'Max'. DO NOT use numbers alone.)\n"
        f"  - 'equipment': string (e.g., 'Chair', 'Resistance Band', 'None')\n"
        f"  - 'duration_per_set': optional string (e.g., '45 sec')\n"
        f"  - 'instructions': list of short tips or guidelines (e.g., ['Support your back', 'Do not twist spine'])\n\n"

        f"Strictly return ONLY the JSON array, with no markdown or extra text."
    )

# 🚀 Create weekly workout plan
@router.post("/workout/plan/week")
async def create_weekly_workout_plan(
    payload: WorkoutDietPlanRequest,
    user_id: str = Depends(get_current_user_id)
):
    if not ObjectId.is_valid(user_id):
        return api_response(message="Unauthorized: Invalid user ID", status=400)

    try:
        # 1️⃣ Delete any existing workout plans for the user
        await workout_collection.delete_many({"user_id": user_id})

        # 2️⃣ Generate new plan from Gemini
        raw_response = await generate_gemini_response(build_workout_prompt(payload))
        cleaned_response = re.sub(r"^```(?:json)?\n|\n```$", "", raw_response.strip())

        try:
            plan_data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            return api_response(message=f"Invalid plan format: {e}", status=400)

        validated_plan = [WorkoutPlanDay(**day) for day in plan_data]

        # 3️⃣ Create new workout plan document
        workout_plan_doc = WorkoutDietPlan(
            user_id=user_id,
            age=payload.age,
            gender=payload.gender,
            height_cm=payload.height_cm,
            weight_kg=payload.weight_kg,
            activity_level=payload.activity_level,
            goal=payload.goal,
            workout_days_per_week=payload.workout_days_per_week,
            workout_duration=payload.workout_duration,
            medical_conditions=payload.medical_conditions,
            injuries_or_limitations=payload.injuries_or_limitations,
            plan=validated_plan
        )

        # 4️⃣ Save to MongoDB
        result = await workout_collection.insert_one(workout_plan_doc.model_dump(by_alias=True))
        inserted_id = str(result.inserted_id)

        return api_response(
            message="Weekly workout plan created successfully",
            status=201,
            data={"plan_id": inserted_id, "plan": validated_plan}
        )

    except Exception as e:
        return api_response(message=f"Failed to generate or save workout plan: {str(e)}", status=500)


# 📋 Get all workout plans for current user
@router.get("/workout/plans/user")
async def get_user_workout_plans(user_id: str = Depends(get_current_user_id)):
    if not ObjectId.is_valid(user_id):
        return api_response(message="Unauthorized: Invalid user ID", status=400)

    plans_cursor = workout_collection.find({"user_id": user_id})
    user_plans = []
    async for plan_doc in plans_cursor:
        plan_doc["_id"] = str(plan_doc["_id"])
        user_plans.append(plan_doc)

    if not user_plans:
        return api_response(message="No workout plans found for this user", status=404)

    return api_response(
        message="User workout plans retrieved successfully",
        status=200,
        data=user_plans
    )

# ❌ Delete a workout plan
@router.delete("/workout/plan/")
async def delete_workout_plans(user_id: str = Depends(get_current_user_id)):
    if not ObjectId.is_valid(user_id):
        return api_response(message="Invalid user ID", status=400)

    delete_result = await workout_collection.delete_many({"user_id": user_id})

    if delete_result.deleted_count == 0:
        return api_response(message="No workout plans found for this user", status=404)

    return api_response(message="All workout plans deleted successfully", status=200)





from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user_id
from app.utils.api_response import api_response
from app.utils.gemini import generate_gemini_response
from app.db.mongodb import db
from bson import ObjectId
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/progress/ai/workout")

@router.get("/generate")
async def generate_ai_workout_progress(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    user_id: str = Depends(get_current_user_id)
):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return api_response(message="Invalid date format. Use YYYY-MM-DD.", status=400)

    if not ObjectId.is_valid(user_id):
        return api_response(message="Invalid user ID", status=400)

    user_obj_id = ObjectId(user_id)

    # ✅ Ensure collection name matches logging route
    logs_cursor = db.workout_completions.find({
        "user_id": user_obj_id,
        "logged_at": {"$gte": start, "$lt": end}
    })

    logs = await logs_cursor.to_list(length=None)

    if not logs:
        return api_response(message="No workout logs found for this date range.", status=404)

    # Fetch user profile
    profile = await db.user_profiles.find_one({"user_id": user_obj_id})
    if not profile:
        return api_response(message="User profile not found.", status=404)

    # Prompt preparation for Gemini
    prompt = f"""
You are a fitness expert AI.
The following is the workout log of a user between {start_date} and {end_date}.
The user profile is:
- Name: {profile.get("name", "Unknown")}
- Age: {profile.get("age")}
- Gender: {profile.get("gender")}
- Height: {profile.get("height_cm")} cm
- Weight: {profile.get("weight_kg")} kg
- Activity Level: {profile.get("activity_level")}
- Goal: {profile.get("goal")}

Workout Logs:
{logs}

Generate a detailed AI progress report in paragraph format including:
- Performance overview
- Missed vs completed days
- Muscle groups focused
- Suggestions for next week
- Motivation note
"""

    ai_response = await generate_gemini_response(prompt)

    return api_response(
        message="AI-generated workout progress report.",
        status=200,
        data={
            "start_date": start_date,
            "end_date": end_date,
            "summary": ai_response
        }
    )
