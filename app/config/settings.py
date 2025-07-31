from pydantic_settings import BaseSettings  # type: ignore
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = Field("WorkoutBuddy", json_schema_extra={"env": "APP_NAME"}) 
    MONGO_URL: str = Field(..., json_schema_extra={"env": "MONGO_URL"})
    DB_NAME: str = Field("workoutbuddy", json_schema_extra={"env": "DB_NAME"})

    GOOGLE_CLIENT_ID: str = Field(..., alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(..., alias="GOOGLE_CLIENT_SECRET")

    SESSION_SECRET_KEY: str = Field(..., alias="SESSION_SECRET_KEY")
    API_SECRET: str = Field(..., alias="API_SECRET") 
    SECRET_KEY: str = Field(..., alias="SECRET_KEY")
    ALGORITHM: str = Field("HS256", alias="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60 * 2, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    FERNET_KEY: str = Field(..., alias="FERNET_KEY")

    # Mailtrap email config
    MAILTRAP_HOST: str = Field("sandbox.smtp.mailtrap.io", json_schema_extra={"env": "MAILTRAP_HOST"})
    MAILTRAP_PORT: int = Field(587, json_schema_extra={"env": "MAILTRAP_PORT"})
    MAILTRAP_USERNAME: str = Field(..., json_schema_extra={"env": "MAILTRAP_USERNAME"})
    MAILTRAP_PASSWORD: str = Field(..., json_schema_extra={"env": "MAILTRAP_PASSWORD"})
    FROM_EMAIL: str = Field(..., json_schema_extra={"env": "FROM_EMAIL"})
    GROQ_API_KEY: str = Field(..., json_schema_extra={"env": "GROQ_API_KEY"})

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

settings = Settings()
