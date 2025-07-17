from pydantic_settings import BaseSettings  # type: ignore
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = Field("WorkoutBuddy", env="APP_NAME")  # ✅ add this
    MONGO_URL: str = Field(..., env="MONGO_URL")
    DB_NAME: str = Field("workoutbuddy", env="DB_NAME")
    GOOGLE_CLIENT_ID: str = Field(..., alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(..., alias="GOOGLE_CLIENT_SECRET")
    SESSION_SECRET_KEY: str = Field(..., alias="SESSION_SECRET_KEY")
    GEMINI_API_KEY: str = Field(..., alias="GEMINI_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
