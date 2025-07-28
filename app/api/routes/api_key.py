from fastapi import APIRouter, status
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from app.schemas.api_key import ApiKeyCreate, ApiKeyOut
from app.core.security import encrypt_api_key, decrypt_api_key
from app.db.mongodb import db
from app.utils.api_response import api_response
from app.config.settings import settings
router = APIRouter()


@router.post("/addApiKey")
async def add_api_key(payload: ApiKeyCreate):
    API_SECRET = settings.API_SECRET
    if not API_SECRET:
        return api_response(
            message="API SECRET not set in environment variables.",
            status=status.HTTP_404_NOT_FOUND
        )

    if payload.secret != API_SECRET:
        return api_response(
            message="Invalid secret.",
            status=status.HTTP_403_FORBIDDEN
        )

    encrypted_key = encrypt_api_key(payload.apiKey)
    new_key = {
        "_id": str(uuid4()),
        "apiKey": encrypted_key,
        "active": True,
        "createdAt": datetime.now(timezone.utc)
    }

    await db["api_keys"].update_many({}, {"$set": {"active": False}})
    await db["api_keys"].insert_one(new_key)
    await db["global"].update_one({"_id": "global"}, {"$set": {"apiHitCount": 0}}, upsert=True)

    return api_response(
        message="API key added successfully.",
        status=status.HTTP_201_CREATED,
        data={**new_key, "apiKey": payload.apiKey}  # return plain API key to user
    )


@router.get("/getApiKey")
async def get_api_key():
    await db["global"].update_one({"_id": "global"}, {"$inc": {"apiHitCount": 1}}, upsert=True)

    active_key = await db["api_keys"].find_one({"active": True})

    # ✅ If no active key, activate the latest one
    if not active_key:
        latest_key = await db["api_keys"].find_one(sort=[("createdAt", -1)])
        if latest_key:
            await db["api_keys"].update_one({"_id": latest_key["_id"]}, {"$set": {"active": True}})
            latest_key["apiKey"] = decrypt_api_key(latest_key["apiKey"])
            await db["global"].update_one({"_id": "global"}, {"$set": {"apiHitCount": 0}})
            return api_response(
                message="No active key found. Activated latest key.",
                status=status.HTTP_200_OK,
                data=latest_key
            )
        else:
            return api_response(
                message="No API keys exist.",
                status=status.HTTP_404_NOT_FOUND
            )

    # ⏱️ Expire after 1 day
    now = datetime.now(timezone.utc)
    created_at = active_key["createdAt"].replace(tzinfo=timezone.utc)
    if now - created_at > timedelta(days=1):
        await db["api_keys"].update_one({"_id": active_key["_id"]}, {"$set": {"active": False}})

        # Rotate to oldest key
        oldest_key = await db["api_keys"].find_one(sort=[("createdAt", 1)])
        if oldest_key:
            await db["api_keys"].update_one({"_id": oldest_key["_id"]}, {"$set": {"active": True}})
            await db["global"].update_one({"_id": "global"}, {"$set": {"apiHitCount": 0}})
            oldest_key["apiKey"] = decrypt_api_key(oldest_key["apiKey"])
            return api_response(
                message="Rotated to oldest API key.",
                status=status.HTTP_200_OK,
                data=oldest_key
            )

        return api_response(
            message="API key expired. No backup key available.",
            status=status.HTTP_400_BAD_REQUEST
        )

    # 🔄 Rotate after 49 hits
    global_doc = await db["global"].find_one({"_id": "global"})
    hit_count = global_doc.get("apiHitCount", 0) if global_doc else 0

    if hit_count >= 49:
        await db["api_keys"].update_one({"_id": active_key["_id"]}, {"$set": {"active": False}})
        oldest_key = await db["api_keys"].find_one(sort=[("createdAt", 1)])
        if oldest_key and oldest_key["_id"] != active_key["_id"]:
            await db["api_keys"].update_one({"_id": oldest_key["_id"]}, {"$set": {"active": True}})
            await db["global"].update_one({"_id": "global"}, {"$set": {"apiHitCount": 0}})
            oldest_key["apiKey"] = decrypt_api_key(oldest_key["apiKey"])
            return api_response(
                message="Rotated to oldest available API key.",
                status=status.HTTP_200_OK,
                data=oldest_key
            )

        return api_response(
            message="API key rotated. No backup key available. Please create a new one.",
            status=status.HTTP_400_BAD_REQUEST
        )

    # ✅ Return the current active key
    active_key["apiKey"] = decrypt_api_key(active_key["apiKey"])
    return api_response(
        message="Active API key retrieved successfully.",
        status=status.HTTP_200_OK,
        data=active_key
    )
