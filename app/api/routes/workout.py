from fastapi import APIRouter, HTTPException
from bson import ObjectId
from typing import List
import json
import re

from app.db.mongodb import db
from app.utils.gemini import generate_gemini_response
from app.utils.api_response import api_response
from app.schemas.workout import WorkoutDietPlanRequest, WorkoutPlanDay
from app.models.workout import WorkoutDietPlan

router = APIRouter()
workout_collection = db["workout_plans"]

# 🔧 Prompt builder
def build_workout_prompt(data: WorkoutDietPlanRequest) -> str:
    return (
        f"You're a professional fitness trainer. Generate a detailed 7-day personalized workout plan in strict JSON format "
        f"for a user with the following attributes:\n"
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

        f"Requirements for the JSON structure (DO NOT include this text in the JSON itself):\n"
        f"- The top-level element must be a JSON array containing exactly 7 objects, one for each day (Monday to Sunday).\n"
        f"- Each day object must have the following keys:\n"
        f"  - 'day': A string representing the day of the week (e.g., 'Monday', 'Tuesday').\n"
        f"  - 'focus': A string describing the primary focus for the day (e.g., 'Chest & Triceps', 'Cardio', 'Rest Day').\n"
        f"  - 'exercises': An array of exercise objects. If it's a 'Rest Day', this array should be empty.\n"
        f"- Each exercise object within the 'exercises' array must have the following keys:\n"
        f"  - 'name': A string for the exercise name (e.g., 'Push-ups', 'Barbell Squats').\n"
        f"  - 'sets': An integer for the number of sets.\n"
        f"  - 'reps': A string for the number of repetitions (e.g., '10-12', '30 seconds', 'Max').\n"
        f"  - 'equipment': A string describing the required equipment (e.g., 'Bodyweight', 'Dumbbells', 'Barbell', 'Treadmill').\n"
        f"  - 'duration_per_set': An optional string for duration if applicable (e.g., '60 sec', '3 min'). Omit if not applicable.\n"
        f"\n"
        f"Generate the plan now. Ensure the output is ONLY the JSON array."
    )

# 🚀 Create weekly workout plan
@router.post("/workout/plan/week")
async def create_weekly_workout_plan(user_id: str, payload: WorkoutDietPlanRequest):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    try:
        raw_response = await generate_gemini_response(build_workout_prompt(payload))
        cleaned_response = re.sub(r"^```(?:json)?\n|\n```$", "", raw_response.strip())

        try:
            plan_data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid plan format: {e}")

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

        result = await workout_collection.insert_one(workout_plan_doc.dict(by_alias=True))
        inserted_id = str(result.inserted_id)

        return api_response(
            message="Weekly workout plan created successfully",
            status=201,
            data={"plan_id": inserted_id, "plan": validated_plan}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate or save workout plan: {e}")

# 📥 Get single workout plan
@router.get("/workout/plan/{plan_id}")
async def get_workout_plan(plan_id: str):
    if not ObjectId.is_valid(plan_id):
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    
    workout_doc = await workout_collection.find_one({"_id": ObjectId(plan_id)})
    if not workout_doc:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    
    workout_doc["_id"] = str(workout_doc["_id"])
    return api_response(
        message="Workout plan retrieved successfully",
        status=200,
        data=workout_doc
    )

# 📋 Get all plans for a user
@router.get("/workout/plans/user/{user_id}")
async def get_user_workout_plans(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    plans_cursor = workout_collection.find({"user_id": user_id})
    user_plans = []
    async for plan_doc in plans_cursor:
        plan_doc["_id"] = str(plan_doc["_id"])
        user_plans.append(plan_doc)
    
    if not user_plans:
        raise HTTPException(status_code=404, detail="No workout plans found for this user.")

    return api_response(
        message="User workout plans retrieved successfully",
        status=200,
        data=user_plans
    )

# ❌ Delete a workout plan
@router.delete("/workout/plan/{plan_id}")
async def delete_workout_plan(plan_id: str):
    if not ObjectId.is_valid(plan_id):
        raise HTTPException(status_code=400, detail="Invalid plan ID")

    delete_result = await workout_collection.delete_one({"_id": ObjectId(plan_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Workout plan not found")
    
    return api_response(
        message="Workout plan deleted successfully",
        status=200
    )
