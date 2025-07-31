from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
import asyncio
from app.config.settings import settings

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]

async def check_mongo_connection():
    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        print("❌ MongoDB connection failed:", e)

# Run the check
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
loop.create_task(check_mongo_connection())
