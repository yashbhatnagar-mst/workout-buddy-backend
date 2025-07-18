import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Local imports
from app.api.api_v1 import api_router
from app.config.settings import settings
from app.db.mongodb import db
from app.api.routes import diet, oauth
from app.api.routes.diet_progress import router as diet_progress_router
from app.api.routes.meal_log import router as meal_log_router
from app.api.routes.api_key import router as api_key_router
from app.utils.gemini import configure_gemini_model

# Initialize FastAPI app
app = FastAPI(title=settings.APP_NAME)

# Middleware: CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware: Session
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "super-secret-key-change-this")
)

# Include routers
app.include_router(diet.router)
app.include_router(api_router, prefix="/api")
app.include_router(oauth.router, prefix="/auth", tags=["OAuth"])
app.include_router(diet_progress_router)
app.include_router(meal_log_router)
app.include_router(api_key_router, prefix="/api-keys", tags=["API Keys"])

# Combined startup event
@app.on_event("startup")
async def on_startup():
    """
    Handles actions to perform on app startup:
    - Configures Gemini model
    - Tests MongoDB connection
    """
    await configure_gemini_model()

    try:
        await db.command("ping")
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Workout Buddy API!"}
