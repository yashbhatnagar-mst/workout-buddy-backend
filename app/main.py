from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config.settings import settings
from app.db.mongodb import db
from app.utils.gemini import configure_gemini_model
from app.api.api_v1 import api_router



app = FastAPI(title=settings.APP_NAME)  

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["FRONTEND_URL", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY)

# Include all routes from api_v1
app.include_router(api_router, prefix="/api")

        
# Startup
@app.on_event("startup")
async def on_startup():
    await configure_gemini_model()
    try:
        await db.command("ping")
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")

# Health check
@app.get("/")
async def root():
    return {"message": "Welcome to Workout Buddy API!"}
