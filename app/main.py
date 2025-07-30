from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config.settings import settings
from app.db.mongodb import db
from app.utils.gemini import configure_gemini_model
from app.api.api_v1 import api_router
from app.api.routes.progress_chart import router as progress_chart_router
from app.api.routes.workout_charts import router as workout_charts_router


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
app.include_router(progress_chart_router, prefix="/api")
app.include_router(workout_charts_router, prefix="/api")

# Health check
@app.get("/")
async def root():
    return {"message": "Welcome to Workout Buddy API!"}
