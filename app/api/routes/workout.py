from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
import json
import re

from app.core.auth import get_current_user_id
from app.db.mongodb import db
from app.utils.gemini import generate_gemini_response
from app.utils.api_response import api_response
from app.schemas.workout import WorkoutDietPlanRequest, WorkoutPlanDay
from app.models.workout import WorkoutDietPlan

router = APIRouter(dependencies=[Depends(get_current_user_id)])
workout_collection = db["workout_plans"]

# 🔧 Prompt builder
def build_workout_prompt(data: WorkoutDietPlanRequest) -> str:
    return (
        f"You are a professional fitness trainer. Generate a detailed 7-day personalized workout plan in valid JSON format "
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

        f"Output Instructions:\n"
        f"- Output ONLY a valid JSON array (no markdown, no explanation, no comments).\n"
        f"- The array must contain exactly 7 objects, one for each day of the week (Monday to Sunday).\n"
        f"- Each object must contain:\n"
        f"  - 'day': A string for the day name (e.g., 'Monday')\n"
        f"  - 'focus': A string describing the workout focus (e.g., 'Chest & Triceps')\n"
        f"  - 'exercises': A list of exercises (empty list if it's a rest day)\n"
        f"- Each exercise must include:\n"
        f"  - 'name': string (e.g., 'Push-ups')\n"
        f"  - 'sets': integer (e.g., 3)\n"
        f"  - 'reps': string (IMPORTANT: must be a string like '10-12', '30 seconds', or 'Max'. DO NOT use numbers.)\n"
        f"  - 'equipment': string (e.g., 'Bodyweight', 'Dumbbells')\n"
        f"  - 'duration_per_set': optional string (e.g., '60 sec', omit if not applicable)\n\n"

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
        raw_response = await generate_gemini_response(build_workout_prompt(payload))
        cleaned_response = re.sub(r"^```(?:json)?\n|\n```$", "", raw_response.strip())

        try:
            plan_data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            return api_response(message=f"Invalid plan format: {e}", status=400)

        validated_plan = [WorkoutPlanDay(**day) for day in plan_data]

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

        result = await workout_collection.insert_one(workout_plan_doc.model_dump(by_alias=True))
        inserted_id = str(result.inserted_id)

        return api_response(
            message="Weekly workout plan created successfully",
            status=201,
            data={"plan_id": inserted_id, "plan": validated_plan}
        )

    except Exception as e:
        return api_response(message=f"Failed to generate or save workout plan: {str(e)}", status=500)

# 📥 Get single workout plan
@router.get("/workout/plan/{plan_id}")
async def get_workout_plan(plan_id: str):
    if not ObjectId.is_valid(plan_id):
        return api_response(message="Invalid plan ID", status=400)

    workout_doc = await workout_collection.find_one({"_id": ObjectId(plan_id)})
    if not workout_doc:
        return api_response(message="Workout plan not found", status=404)

    workout_doc["_id"] = str(workout_doc["_id"])
    return api_response(
        message="Workout plan retrieved successfully",
        status=200,
        data=workout_doc
    )

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
@router.delete("/workout/plan/{plan_id}")
async def delete_workout_plan(plan_id: str):
    if not ObjectId.is_valid(plan_id):
        return api_response(message="Invalid plan ID", status=400)

    delete_result = await workout_collection.delete_one({"_id": ObjectId(plan_id)})
    if delete_result.deleted_count == 0:
        return api_response(message="Workout plan not found", status=404)

    return api_response(message="Workout plan deleted successfully", status=200)
