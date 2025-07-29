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
        profile = log.get("dietProgressReport", {}).get("userProfile", {})
        if profile.get("weight"):
            last_weight = profile["weight"]
            break

    daily_chart_data = []
    consistency_count = 0
    adherence_scores = []

    for entry in sorted_logs:
        date = entry.get("date")
        breakfast = entry.get("breakfast", 0)
        lunch = entry.get("lunch", 0)
        dinner = entry.get("dinner", 0)
        total = entry.get("total", 0)

        # Adherence: assume 100 if all meals are logged
        adherence = 100 if all(m > 0 for m in [breakfast, lunch, dinner]) else 0

        if adherence > 0:
            consistency_count += 1
            adherence_scores.append(adherence)

        daily_chart_data.append({
            "date": date,
            "total": total
        })

    consistency_percentage = round((consistency_count / len(sorted_logs)) * 100, 2)
    adherence_percentage = round(sum(adherence_scores) / len(adherence_scores), 2) if adherence_scores else 0.0

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
