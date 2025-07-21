from fastapi import APIRouter, HTTPException, status
from app.db.mongodb import db
from app.utils.api_response import api_response
from bson import ObjectId
from app.schemas.user_profile import UserProfileCreate, UserProfileUpdate
from app.models.user_profile import UserProfile

router = APIRouter()

users_collection = db["users"]
profiles_collection = db["user_profiles"]

@router.post("/user/{user_id}/profile")
async def create_user_profile(user_id: str, payload: UserProfileCreate):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_profile = await profiles_collection.find_one({"user_id": user_id})
    if existing_profile:
        raise HTTPException(status_code=409, detail="User profile already exists")

    # 🔁 Build full profile object
    profile = UserProfile(
        user_id=user_id,
        full_name=payload.full_name,
        age=payload.age,
        gender=payload.gender,
        height=payload.height,
        weight=payload.weight,
        activity_level=payload.activity_level,
        goal=payload.goal
        # `email` is not in the model yet, but you could add it
    )

    await profiles_collection.insert_one(profile.model_dump(by_alias=True))

    return api_response(
        message="User profile created successfully",
        status=status.HTTP_201_CREATED,
        data={"profile_id": str(profile.id)}
    )

@router.get("/user/{user_id}/profile")
async def get_user_profile(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    profile = await profiles_collection.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    profile["_id"] = str(profile["_id"])
    return api_response(
        message="User profile fetched successfully",
        status=status.HTTP_200_OK,
        data=profile
    )

@router.patch("/user/{user_id}/profile")
async def update_user_profile(user_id: str, payload: UserProfileUpdate):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    profile = await profiles_collection.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    update_data = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    await profiles_collection.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )

    updated_profile = await profiles_collection.find_one({"user_id": user_id})
    updated_profile["_id"] = str(updated_profile["_id"])

    return api_response(
        message="User profile updated successfully",
        status=status.HTTP_200_OK,
        data=updated_profile
    )
