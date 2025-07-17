from motor.motor_asyncio import AsyncIOMotorClient # type: ignore #type
from app.config.settings import settings

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]
