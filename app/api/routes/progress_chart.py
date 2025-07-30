from fastapi import APIRouter, Depends
from bson import ObjectId
from app.db.mongodb import db
from app.core.auth import get_current_user_id
from app.utils.api_response import api_response

router = APIRouter()
diet_logs_collection = db["diet_progress_logs"]

@router.get("/progress/diet/chart/progress")
async def get_diet_chart_data(user_id: str = Depends(get_current_user_id)):
    logs = await diet_logs_collection.find({"user_id": ObjectId(user_id)}).to_list(None)

    if not logs:
        return api_response(
            message="No diet progress data found.",
            status=404
        )

    # Flatten all daily logs from all entries
    all_entries = []
    for log in logs:
        data_log = log.get("generated_summary", {})
        daily_logs = data_log.get("dietProgressReport", {}).get("estimatedCalorieBreakdown", {}).get("dailyLog", [])
        for entry in daily_logs:
            if "calories" in entry:
                all_entries.append({
                    "date": entry.get("date"),
                    "breakfast": entry["calories"].get("breakfast", 0),
                    "lunch": entry["calories"].get("lunch", 0),
                    "dinner": entry["calories"].get("dinner", 0),
                    "total": entry["calories"].get("total", 0),
                })

    if not all_entries:
        return api_response(message="No daily calorie logs found.", status=404)

    # Sort and slice last 15 days
    sorted_logs = sorted(all_entries, key=lambda x: x.get("date"), reverse=True)[:15]
    sorted_logs.reverse()

    # Get weight from latest userProfile
    last_weight = "N/A"
    for log in reversed(logs):
        profile = log.get("generated_summary", {}).get("dietProgressReport", {}).get("userProfile", {})
        if profile.get("weight"):
            last_weight = profile["weight"]
            break

    # ✅ Get adherence and consistency from latest available summary
    adherence_percentage = 0.0
    consistency_percentage = 0.0
    for log in reversed(logs):
        report = log.get("generated_summary", {}).get("dietProgressReport", {})
        adherence_data = report.get("adherenceAnalysis", {})
        consistency_data = report.get("mealLoggingConsistency", {})

        if adherence_data.get("adherencePercentage") is not None and consistency_data.get("consistencyPercentage") is not None:
            adherence_percentage = adherence_data.get("adherencePercentage", 0.0)
            consistency_percentage = consistency_data.get("consistencyPercentage", 0.0)
            break

    # Daily chart data (only total calories per day)
    daily_chart_data = []
    for entry in sorted_logs:
        daily_chart_data.append({
            "date": entry.get("date"),
            "total": entry.get("total", 0)
        })

    response_data = {
        "period": f"{sorted_logs[0]['date']} to {sorted_logs[-1]['date']}",
        "weight": last_weight,
        "consistency_percentage": consistency_percentage,
        "adherence_percentage": adherence_percentage,
        "daily_chart_data": daily_chart_data
    }

    return api_response(
        message="Diet chart progress generated successfully.",
        status=200,
        data=response_data
    )
