from fastapi import APIRouter
from app.schemas.diet_progress_schema import WeeklyProgressResponse, MonthlyProgressResponse, DailyProgress
from app.db.mongodb import db
from bson import ObjectId
from datetime import datetime, timedelta , timezone
from typing import List


router = APIRouter(prefix="/api/progress", tags=["Diet Progress"])


def estimate_calories(meal: str):
    if meal:
        return 600  # Dummy static value
    return 0


@router.get("/diet/daily", response_model=List[DailyProgress])
async def get_daily_diet_progress(user_id: str):
    today = datetime.now(timezone.utc).date()
    past_seven = today - timedelta(days=7)

    logs_cursor = db["meal_logs"].find({
        "user_id": ObjectId(user_id)
    })

    daily_progress = []

    async for log in logs_cursor:
        date_obj = datetime.fromisoformat(log["date"]).date()
        if past_seven <= date_obj <= today:
            meals = log["meals"]
            calories = sum(estimate_calories(meals.get(k)) for k in ["breakfast", "lunch", "dinner"])
            missed = sum(1 for k in ["breakfast", "lunch", "dinner"] if not meals.get(k))

            daily_progress.append({
                "date": date_obj.isoformat(),
                "total_calories": calories,
                "target_calories": 1800,
                "adherence_percent": round((calories / 1800) * 100, 2),
                "missed_meals_count": missed
            })

    return sorted(daily_progress, key=lambda x: x["date"])


@router.get("/diet/weekly", response_model=List[WeeklyProgressResponse])
async def get_weekly_diet_progress(user_id: str):
    logs_cursor = db["meal_logs"].find({
        "user_id": ObjectId(user_id)
    })

    weekly_data = {}

    async for log in logs_cursor:
        date_obj = datetime.fromisoformat(log["date"]).date()
        monday = (date_obj - timedelta(days=date_obj.weekday()))
        sunday = monday + timedelta(days=6)
        key = (monday.isoformat(), sunday.isoformat())

        meals = log["meals"]
        calories = sum(estimate_calories(meals.get(k)) for k in ["breakfast", "lunch", "dinner"])
        missed = sum(1 for k in ["breakfast", "lunch", "dinner"] if not meals.get(k))

        if key not in weekly_data:
            weekly_data[key] = {
                "total_calories": 0,
                "target_calories": 0,
                "adherence_sum": 0,
                "days_count": 0,
                "missed_meals": 0,
                "daily_breakdown": []
            }

        week = weekly_data[key]
        week["total_calories"] += calories
        week["target_calories"] += 1800
        week["adherence_sum"] += round((calories / 1800) * 100, 2)
        week["missed_meals"] += missed
        week["days_count"] += 1
        week["daily_breakdown"].append({
            "date": date_obj.isoformat(),
            "total_calories": calories,
            "target_calories": 1800,
            "adherence_percent": round((calories / 1800) * 100, 2),
            "missed_meals_count": missed
        })

    result = []
    for (start, end), data in weekly_data.items():
        result.append({
            "week_start_date": start,
            "week_end_date": end,
            "total_calories": data["total_calories"],
            "target_calories": data["target_calories"],
            "average_adherence": round(data["adherence_sum"] / data["days_count"], 2),
            "missed_meals": data["missed_meals"],
            "daily_breakdown": data["daily_breakdown"]
        })

    return result


@router.get("/diet/monthly", response_model=List[MonthlyProgressResponse])
async def get_monthly_diet_progress(user_id: str):
    logs_cursor = db["meal_logs"].find({
        "user_id": ObjectId(user_id)
    })

    month_data = {}

    async for log in logs_cursor:
        date_obj = datetime.fromisoformat(log["date"])
        month_label = date_obj.strftime("%B %Y")

        meals = log["meals"]
        calories = sum(estimate_calories(meals.get(k)) for k in ["breakfast", "lunch", "dinner"])
        missed = sum(1 for k in ["breakfast", "lunch", "dinner"] if not meals.get(k))

        if month_label not in month_data:
            month_data[month_label] = {
                "total_calories": 0,
                "target_calories": 0,
                "adherence_sum": 0,
                "days_count": 0,
                "missed_meals": 0,
                "daily_breakdown": []
            }

        month = month_data[month_label]
        month["total_calories"] += calories
        month["target_calories"] += 1800
        month["adherence_sum"] += round((calories / 1800) * 100, 2)
        month["missed_meals"] += missed
        month["days_count"] += 1
        month["daily_breakdown"].append({
            "date": date_obj.isoformat(),
            "total_calories": calories,
            "target_calories": 1800,
            "adherence_percent": round((calories / 1800) * 100, 2),
            "missed_meals_count": missed
        })

    result = []
    for month, data in month_data.items():
        result.append({
            "month": month,
            "total_calories": data["total_calories"],
            "target_calories": data["target_calories"],
            "average_adherence": round(data["adherence_sum"] / data["days_count"], 2),
            "missed_meals": data["missed_meals"],
            "daily_breakdown": data["daily_breakdown"]
        })

    return result
