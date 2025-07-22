from fastapi import APIRouter
from app.schemas.api_response_schema import APIResponse
from app.schemas.diet_progress_schema import DailyProgress, WeeklyProgressResponse, MonthlyProgressResponse
from app.db.mongodb import db
from bson import ObjectId
from datetime import datetime, timedelta , timezone
from typing import List
from app.utils.api_response import api_response

router = APIRouter(prefix="/api/progress", tags=["Diet Progress"])


def extract_day_data(day_obj):
    meals = day_obj.get("meals", {})
    calories = sum(estimate_calories(meals.get(k)) for k in ["breakfast", "lunch", "dinner"])
    missed = sum(1 for k in ["breakfast", "lunch", "dinner"] if not meals.get(k))
    return calories, 1800, round((calories / 1800) * 100, 2), missed


def estimate_calories(meal: str):
    if meal:
        return 600  # Dummy estimate
    return 0


@router.get("/diet/daily", response_model=APIResponse[List[DailyProgress]])
async def get_daily_diet_progress(user_id: str):
    today = datetime.now(timezone.utc).date()
    past_seven = today - timedelta(days=7)

    plans = db["diet_plans"].find({"user_id": ObjectId(user_id)})

    daily_progress = []
    async for plan in plans:
        for day_data in plan["ai_generated_plan"].values():
            date = datetime.fromisoformat(day_data["date"]).date()
            if past_seven <= date <= today:
                calories, target, adherence, missed = extract_day_data(day_data)
                daily_progress.append({
                    "date": date.isoformat(),
                    "total_calories": calories,
                    "target_calories": target,
                    "adherence_percent": adherence,
                    "missed_meals_count": missed
                })

    return api_response(
        message="Daily diet progress fetched successfully",
        status=200,
        data=daily_progress
    )


@router.get("/diet/weekly", response_model=APIResponse[List[WeeklyProgressResponse]])
async def get_weekly_diet_progress(user_id: str):
    plans = db["diet_plans"].find({"user_id": ObjectId(user_id)})

    weekly_progress = []

    async for plan in plans:
        week_start = plan["week_start_date"]
        week_end = plan["week_end_date"]

        total_calories = 0
        target_calories = 0
        adherence_sum = 0
        missed_meals = 0
        breakdown = []

        for day_data in plan["ai_generated_plan"].values():
            calories, target, adherence, missed = extract_day_data(day_data)
            breakdown.append({
                "date": day_data["date"],
                "total_calories": calories,
                "target_calories": target,
                "adherence_percent": adherence,
                "missed_meals_count": missed
            })
            total_calories += calories
            target_calories += target
            adherence_sum += adherence
            missed_meals += missed

        avg_adherence = adherence_sum / 7

        weekly_progress.append({
            "week_start_date": week_start,
            "week_end_date": week_end,
            "total_calories": total_calories,
            "target_calories": target_calories,
            "average_adherence": round(avg_adherence, 2),
            "missed_meals": missed_meals,
            "daily_breakdown": breakdown
        })

    return api_response(
        message="Weekly diet progress fetched successfully",
        status=200,
        data=weekly_progress
    )


@router.get("/diet/monthly", response_model=APIResponse[List[MonthlyProgressResponse]])
async def get_monthly_diet_progress(user_id: str):
    plans = db["diet_plans"].find({"user_id": ObjectId(user_id)})

    month_groups = {}

    async for plan in plans:
        for day_data in plan["ai_generated_plan"].values():
            date_obj = datetime.fromisoformat(day_data["date"])
            month_label = date_obj.strftime("%B %Y")

            calories, target, adherence, missed = extract_day_data(day_data)

            if month_label not in month_groups:
                month_groups[month_label] = {
                    "total_calories": 0,
                    "target_calories": 0,
                    "adherence_sum": 0,
                    "days_count": 0,
                    "missed_meals": 0,
                    "daily_breakdown": []
                }

            m = month_groups[month_label]
            m["total_calories"] += calories
            m["target_calories"] += target
            m["adherence_sum"] += adherence
            m["missed_meals"] += missed
            m["days_count"] += 1
            m["daily_breakdown"].append({
                "date": day_data["date"],
                "total_calories": calories,
                "target_calories": target,
                "adherence_percent": adherence,
                "missed_meals_count": missed
            })

    monthly_progress = []
    for month, data in month_groups.items():
        monthly_progress.append({
            "month": month,
            "total_calories": data["total_calories"],
            "target_calories": data["target_calories"],
            "average_adherence": round(data["adherence_sum"] / data["days_count"], 2),
            "missed_meals": data["missed_meals"],
            "daily_breakdown": data["daily_breakdown"]
        })

    return api_response(
        message="Monthly diet progress fetched successfully",
        status=200,
        data=monthly_progress
    )
