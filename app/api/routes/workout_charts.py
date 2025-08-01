from fastapi import APIRouter, Depends
from bson import ObjectId
from app.core.auth import get_current_user_id
from app.db.mongodb import db
from app.utils.api_response import api_response
from app.schemas.workout_charts import (
    WorkoutProgressAPIResponse,
    WorkoutProgressResponse,
    WorkoutProgressSummary,
    MuscleDistribution,
    Tip,
    DailyBurnout
)

router = APIRouter()
workout_logs = db["workout_progress_logs"]

@router.get("/workout/progress/report", response_model=WorkoutProgressAPIResponse)
async def get_workout_progress_summary(user_id: str = Depends(get_current_user_id)):
    try:
        log = await workout_logs.find_one({"user_id": ObjectId(user_id)})
        if not log or "generated_summary" not in log:
            return api_response(
                success=False,
                message="No workout progress summary found.",
                status=404,
                data=None
            )

        summary_data = log["generated_summary"]

        # Construct daily burnout list
        daily_logs = summary_data.get("dailyLog", [])
        daily_burnout_logs = [DailyBurnout(**entry) for entry in daily_logs]

        # Construct response
        response = WorkoutProgressResponse(
            start_date=summary_data.get("start_date", ""),
            end_date=summary_data.get("end_date", ""),
            summary=WorkoutProgressSummary(
                start_date=summary_data.get("start_date", ""),
                end_date=summary_data.get("end_date", ""),
                completed_days=summary_data.get("completed_days", 0),
                total_days=summary_data.get("total_days", 0),
                consistency=summary_data.get("consistency", 0.0),
                average_rpe=summary_data.get("average_rpe", 0.0),
                total_sets=summary_data.get("total_sets", 0),
                total_reps=summary_data.get("total_reps", 0),
                calories_burned=summary_data.get("calories_burned", 0),
                dailyLog=daily_burnout_logs,
                sum_of_all_calorie_burnout=summary_data.get("sum_of_all_calorie_burnout", 0),
                muscle_distribution=MuscleDistribution(**summary_data.get("muscle_distribution", {})),
                weight=summary_data.get("weight", 0),
                tips=[Tip(**tip) for tip in summary_data.get("tips", [])]
                
            )
        )

        return api_response(
            message="Workout progress summary fetched successfully.",
            status=200,
            data=response
        )

    except Exception as e:
        return api_response(
            message=f"Error retrieving workout progress summary: {str(e)}",
            status=500,
            data=None
        )
