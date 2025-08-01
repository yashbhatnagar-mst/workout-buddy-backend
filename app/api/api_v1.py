from fastapi import APIRouter

# Import all route modules
from app.api.routes import (
    auth,
    oauth,
    users,
    workout,
    forgot_password,
    diet,
    chat
)
from app.api.routes.diet_progress_routes import router as diet_progress_router
from app.api.routes.delete_diet_plan_router import router as delete_diet_plan_router
from app.api.routes.meal_log_routes import router as meal_log_router
from app.api.routes.api_key import router as api_key_router
from app.api.routes.delete_meal_log import router as delete_meal_log_router
from app.api.routes.update_meal_log import router as update_meal_log_router
from app.api.routes.workout_progress import router as workout_progress_router
from app.api.routes.progress_chart import router as progress_chart_router
from app.api.routes.workout_charts import router as workout_charts_router

# Main API v1 router
api_router = APIRouter()

# Include all routers under api_router
api_router.include_router(auth.router, tags=["Auth"])
api_router.include_router(oauth.router, tags=["OAuth"])
api_router.include_router(forgot_password.router, tags=["Forgot Password"])
api_router.include_router(users.router, tags=["Users"])
api_router.include_router(chat.router, tags=["Chatbot"])
api_router.include_router(workout.router, tags=["Workout"])
api_router.include_router(diet.router, tags=["Diet"])
api_router.include_router(delete_diet_plan_router, tags=["Diet"])
api_router.include_router(meal_log_router, prefix="/progress", tags=["Meal Log"])
api_router.include_router(delete_meal_log_router, tags=["Meal Log"])
api_router.include_router(update_meal_log_router, tags=["Meal Log"])
api_router.include_router(diet_progress_router, prefix="/progress", tags=["Diet Progress"])
api_router.include_router(workout_progress_router, prefix="/progress", tags=["Workout Progress"])
api_router.include_router(api_key_router, prefix="/api-keys", tags=["API Keys"])
api_router.include_router(progress_chart_router,  tags=["Progress Charts"])
api_router.include_router(workout_charts_router,  tags=["Progress Charts"])
