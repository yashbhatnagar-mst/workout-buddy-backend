import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from app.api.api_v1 import api_router
from app.config.settings import settings
from app.db.mongodb import db
from app.api.routes import diet, oauth
from app.api.routes.diet_progress import router as diet_progress_router
from app.api.routes.meal_log import router as meal_log_router

# -------------------- Load Environment Variables --------------------
load_dotenv()

# -------------------- Initialize FastAPI App --------------------
app = FastAPI(title=settings.APP_NAME)

# -------------------- CORS Middleware --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Session Middleware --------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "super-secret-key-change-this")
)

# -------------------- Include Routers --------------------
app.include_router(diet.router)
app.include_router(api_router, prefix="/api")
app.include_router(oauth.router, prefix="/auth", tags=["OAuth"])
app.include_router(diet_progress_router)
app.include_router(meal_log_router)

# -------------------- MongoDB Health Check on Startup --------------------
@app.on_event("startup")
async def test_db_connection():
    try:
        await db.command("ping")
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")

# -------------------- Default Root Endpoint --------------------
@app.get("/")
async def root():
    return {"message": "Welcome to Workout Buddy API!"}
