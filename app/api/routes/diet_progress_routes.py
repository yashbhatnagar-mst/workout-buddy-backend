from fastapi import APIRouter, Query , Depends
from app.core.auth import get_current_user_id
from app.schemas.api_response_schema import APIResponse
from app.schemas.diet_progress_schema import DailyProgress, WeeklyProgressResponse, MonthlyProgressResponse
from app.db.mongodb import db
from datetime import datetime
from typing import List
from app.utils.api_response import api_response
from bson import ObjectId

router = APIRouter(tags=["Diet Progress"])


def extract_meal_data(meals):
    calories = sum(600 for meal in ["breakfast", "lunch", "dinner"] if meals.get(meal))
    missed = sum(1 for meal in ["breakfast", "lunch", "dinner"] if not meals.get(meal))
    return calories, 1800, round((calories / 1800) * 100, 2), missed


@router.get("/diet/daily", response_model=APIResponse[List[DailyProgress]])
async def get_daily_progress(user_id: str = Depends(get_current_user_id), date: str = Query(..., description="YYYY-MM-DD")):
    try:
        datetime.fromisoformat(date)
    except ValueError:
        return api_response(message="Invalid date format.", status=400, success=False, data=None)

    logs = db["meal_logs"].find({"user_id": ObjectId(user_id), "date": date})
    daily_progress = []

    async for log in logs:
        calories, target, adherence, missed = extract_meal_data(log["meals"])
        daily_progress.append({
            "date": date,
            "total_calories": calories,
            "target_calories": target,
            "adherence_percent": adherence,
            "missed_meals_count": missed
        })

    if not daily_progress:
        return api_response(message="No meal logs found for this date.", status=404, success=False, data=[])

    return api_response(
        message="Daily progress fetched successfully.",
        status=200,
        data=daily_progress
    )


@router.get("/diet/weekly", response_model=APIResponse[List[WeeklyProgressResponse]])
async def get_weekly_progress( start_date: str, end_date: str , user_id: str = Depends(get_current_user_id)):
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        if start > end:
            raise ValueError
    except ValueError:
        return api_response(message="Invalid date range.", status=400, success=False, data=None)

    logs = db["meal_logs"].find({
        "user_id": ObjectId(user_id),
        "date": {"$gte": start_date, "$lte": end_date}
    })

    dates_seen = set()
    daily_breakdown = []
    total_calories = target_calories = adherence_sum = missed_meals = 0
    days_count = 0

    async for log in logs:
        log_date = log["date"]
        if log_date in dates_seen:
            continue
        dates_seen.add(log_date)

        calories, target, adherence, missed = extract_meal_data(log["meals"])
        daily_breakdown.append({
            "date": log_date,
            "total_calories": calories,
            "target_calories": target,
            "adherence_percent": adherence,
            "missed_meals_count": missed
        })
        total_calories += calories
        target_calories += target
        adherence_sum += adherence
        missed_meals += missed
        days_count += 1

    if not daily_breakdown:
        return api_response(message="No meal logs found in this range.", status=404, success=False, data=[])

    avg_adherence = round(adherence_sum / days_count, 2) if days_count else 0

    return api_response(
        message="Weekly progress fetched successfully.",
        status=200,
        data=[{
            "start_date": start_date,
            "end_date": end_date,
            "total_calories": total_calories,
            "target_calories": target_calories,
            "average_adherence": avg_adherence,
            "missed_meals": missed_meals,
            "daily_breakdown": daily_breakdown
        }]
    )


@router.get("/diet/monthly", response_model=APIResponse[List[MonthlyProgressResponse]])
async def get_monthly_progress(start_date: str, end_date: str , user_id: str = Depends(get_current_user_id)):
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        if start > end:
            raise ValueError
    except ValueError:
        return api_response(message="Invalid date range.", status=400, success=False, data=None)

    logs = db["meal_logs"].find({
        "user_id": ObjectId(user_id),
        "date": {"$gte": start_date, "$lte": end_date}
    })

    dates_seen = set()
    daily_breakdown = []
    total_calories = target_calories = adherence_sum = missed_meals = 0
    days_count = 0

    async for log in logs:
        log_date = log["date"]
        if log_date in dates_seen:
            continue
        dates_seen.add(log_date)

        calories, target, adherence, missed = extract_meal_data(log["meals"])
        daily_breakdown.append({
            "date": log_date,
            "total_calories": calories,
            "target_calories": target,
            "adherence_percent": adherence,
            "missed_meals_count": missed
        })
        total_calories += calories
        target_calories += target
        adherence_sum += adherence
        missed_meals += missed
        days_count += 1

    if not daily_breakdown:
        return api_response(message="No meal logs found in this range.", status=404, success=False, data=[])

    avg_adherence = round(adherence_sum / days_count, 2) if days_count else 0

    return api_response(
        message="Monthly progress fetched successfully.",
        status=200,
        data=[{
            "start_date": start_date,
            "end_date": end_date,
            "total_calories": total_calories,
            "target_calories": target_calories,
            "average_adherence": avg_adherence,
            "missed_meals": missed_meals,
            "daily_breakdown": daily_breakdown
        }]
    )
