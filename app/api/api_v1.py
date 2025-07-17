from fastapi import APIRouter
from app.api.routes import auth
from app.api.routes import users
from app.api.routes import workout

api_router = APIRouter()
api_router.include_router(auth.router ,tags=["Auth"])
api_router.include_router(users.router ,tags=["Users"])
api_router.include_router(workout.router ,tags=["Workout"])
