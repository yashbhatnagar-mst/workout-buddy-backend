from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Local imports
from app.config.settings import settings
from app.db.mongodb import db
from app.utils.gemini import configure_gemini_model
from app.api.api_v1 import api_router
from app.api.routes import diet, oauth
from app.api.routes.diet_progress_routes import router as diet_progress_router 
from app.api.routes.delete_diet_plan_router import router as delete_diet_plan_router
from app.api.routes.meal_log_routes import router as meal_log_router
from app.api.routes.api_key import router as api_key_router
from app.api.routes.delete_meal_log import router as delete_meal_log_router
from app.api.routes.update_meal_log import router as update_meal_log_router
from app.api.routes.forgot_password import router as forgot_password_route
from app.config.settings import settings

# FastAPI instance
app = FastAPI(title=settings.APP_NAME)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["FRONTEND_URL", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session Middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY
)

# Routes
app.include_router(diet.router)
app.include_router(delete_diet_plan_router)
app.include_router(meal_log_router, prefix="/api/progress", tags=["Meal Log"])
app.include_router(delete_meal_log_router)
app.include_router(update_meal_log_router)
app.include_router(api_router, prefix="/api")
app.include_router(oauth.router, prefix="/auth", tags=["OAuth"])
app.include_router(diet_progress_router, prefix="/api/progress", tags=["Diet Progress"])
app.include_router(api_key_router, prefix="/api-keys", tags=["API Keys"])
app.include_router(forgot_password_route, tags=["Forgot Password"])


# Startup event: DB + Gemini AI
@app.on_event("startup")
async def on_startup():
    await configure_gemini_model()
    try:
        await db.command("ping")
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")


# Root Health Check
@app.get("/")
async def root():
    return {"message": "Welcome to Workout Buddy API!"}
