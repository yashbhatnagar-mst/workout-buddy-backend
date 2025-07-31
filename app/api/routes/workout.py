from fastapi import APIRouter, Depends
from bson import ObjectId
import json
import re
from app.core.auth import get_current_user_id
from app.db.mongodb import db
from app.utils.api_response import api_response
from app.schemas.workout import WorkoutDietPlanRequest, WorkoutPlanDay , WorkoutDayLogRequest
from app.models.workout import WorkoutDietPlan
from datetime import datetime, timezone , time , timedelta ,date
from app.models.user_profile import UserProfileUpdate

from app.utils.groq import get_groq_response


router = APIRouter(dependencies=[Depends(get_current_user_id)])
workout_collection = db["workout_plans"]
workout_log_collection = db["workout_completions"]
profiles_collection = db["user_profiles"]
# 🔧 Prompt builder
def build_workout_prompt(data: WorkoutDietPlanRequest) -> str:
    return (
        f"You are a certified physiotherapist and fitness trainer specializing in injury recovery and adaptive workouts. Generate a safe, effective, and detailed 7-day personalized workout plan in valid JSON format "
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
        f"- If the user has **serious injuries** (e.g., broken leg, spinal issues, missing limb), the plan MUST avoid strain on those areas.\n"
        f"- Use adaptive, low-impact, or seated/rehab exercises as needed.\n"
        f"- ✅ Assign exercises **strictly for all days mentioned** — do **not reduce** the number of days or add rest days on your own.\n"

        f"- Do NOT assign exercises that can aggravate the injuries or limitations.\n"
        f"- Emphasize safety and proper form in all instructions.\n"
        f"- ⚠️ If the user has **less than 6 workout days per week**, assign REST days for the remaining days. Always prioritize assigning rest to **Sunday first, then Saturday, then other weekdays**.\n"
        f"- ⚠️ On rest days, DO NOT include any exercises – the 'exercises' list should be empty.\n\n"

        f"Output Instructions:\n"
        f"- Output ONLY a valid JSON array (no markdown, no explanation, no comments).\n"
        f"- The array must contain exactly 7 objects, one for each day of the week (Monday to Sunday).\n"
        f"- Each object must contain:\n"
        f"  - 'day': A string for the day name (e.g., 'Monday')\n"
        f"  - 'focus': A string describing the workout focus (e.g., 'Upper Body Mobility', 'Recovery', or 'Rest')\n"
        f"  - 'exercises': A list of exercises (empty list if it's a rest day)\n"
        f"- Each exercise must include:\n"
        f"  - 'name': string (e.g., 'Seated Arm Circles')\n"
        f"  - 'sets': integer (e.g., 2)\n"
        f"  - 'reps': string (e.g., '10-12', '30 seconds', or 'Max'. DO NOT use numbers alone.)\n"
        f"  - 'equipment': string (e.g., 'Chair', 'Resistance Band' )\n"
        f"  - 'duration_per_set': string (e.g., '45 sec')\n"
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


        raw_response = get_groq_response(build_workout_prompt(payload))
        cleaned_response = re.sub(r"^```(?:json)?\n|\n```$", "", raw_response.strip())

        # 🔍 Check for empty or invalid response
        if not cleaned_response:
            return api_response(message="Empty response from Groq model", status=502)

        try:
            plan_data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            return api_response(
                message="Invalid JSON from Groq response",
                status=400,
                data={"raw_response": raw_response}
            )

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

        user_profile_docs = UserProfileUpdate(
            user_id=user_id,
            age=payload.age,
            gender=payload.gender,
            height=payload.height_cm,
            weight=payload.weight_kg,
            activity_level=payload.activity_level,
            goal=payload.goal
        )
        # 4️⃣ Save to MongoDB
        await profiles_collection.update_one(
            {"user_id": user_id},
            {"$set": user_profile_docs.model_dump(exclude_unset=True)}
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


@router.post("/workout/complete")
async def log_workout_day(
    payload: WorkoutDayLogRequest,
    user_id: str = Depends(get_current_user_id)
):
    if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(payload.plan_id):
        return api_response(message="Invalid user ID or plan ID", status=400)

    # 🔎 Fetch workout plan
    plan_doc = await workout_collection.find_one({
        "_id": ObjectId(payload.plan_id),
        "user_id": user_id
    })

    if not plan_doc:
        return api_response(message="Workout plan not found", status=404)

    # 🗓 Get day name from date (e.g., "Sunday")
    day_name = payload.date.strftime("%A")

    # 🔍 Find matching day from the plan
    day_plan = next(
        (d for d in plan_doc.get("plan", []) if d.get("day", "").lower() == day_name.lower()),
        None
    )

    if not day_plan:
        return api_response(message=f"No workout found for day: {day_name}", status=404)
    
    if payload.date > date.today():
        return api_response(message="Cannot log workout for a future date.", status=400)

    # 🚫 Prevent logging rest day
    if not day_plan.get("exercises") or day_plan.get("focus", "").lower() == "rest":
        return api_response(message=f"{day_name} is a rest day. No workout to log.", status=400)


    log_timestamp = payload.created_at or datetime.now(timezone.utc)

    # 📆 Check for duplicates using logged_at range
    start_dt = datetime.combine(payload.date, time.min).replace(tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)

    existing_log = await workout_log_collection.find_one({
        "user_id": ObjectId(user_id),
        "plan_id": ObjectId(payload.plan_id),
        "logged_at": {"$gte": start_dt, "$lt": end_dt}
    })

    if existing_log:
        return api_response(message=f"Workout for {payload.date} already logged.", status=409)

    # ✅ Map exercises
    completion_flags = {e.name.lower(): e.completed for e in (payload.exercises or [])}
    mapped_exercises = []
    for exercise in day_plan.get("exercises", []):
        mapped_exercises.append({
            "name": exercise["name"],
            "sets": exercise["sets"],
            "reps": exercise["reps"],
            "equipment": exercise.get("equipment"),
            "duration_per_set": exercise.get("duration_per_set"),
            "completed": completion_flags.get(exercise["name"].lower(), False)
        })

    # 🧾 Final log document
    log_doc = {
        "user_id": ObjectId(user_id),
        "plan_id": ObjectId(payload.plan_id),
        "date": payload.date.isoformat(),
        "status": payload.status,
        "logged_at": log_timestamp,
        "exercises": mapped_exercises
    }

    try:
        result = await workout_log_collection.insert_one(log_doc)
        return api_response(
            message=f"Workout for {payload.date} logged with {len(mapped_exercises)} exercises.",
            status=201,
            data={"log_id": str(result.inserted_id)}
        )
    except Exception as e:
        return api_response(message=f"Error logging workout: {str(e)}", status=500)
