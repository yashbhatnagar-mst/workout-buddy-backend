from fastapi import APIRouter, Depends, Body, status
from app.core.auth import get_current_user_id
from app.db.mongodb import db
from app.utils.api_response import api_response
from bson import ObjectId
from app.schemas.user_profile import UserProfileCreate, UserProfileUpdate
from app.models.user_profile import UserProfile

router = APIRouter()

users_collection = db["users"]
profiles_collection = db["user_profiles"]

def is_valid_object_id(user_id: str) -> bool:
    return ObjectId.is_valid(user_id)

@router.post("/user/profile")
async def create_user_profile(
    user_id: str = Depends(get_current_user_id),
    payload: UserProfileCreate = Body(...)
):
    if not is_valid_object_id(user_id):
        return api_response("Invalid user ID", status.HTTP_400_BAD_REQUEST)

    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return api_response("User not found", status.HTTP_404_NOT_FOUND)

    existing_profile = await profiles_collection.find_one({"user_id": user_id})
    if existing_profile:
        return api_response("User profile already exists", status.HTTP_409_CONFLICT)

    profile = UserProfile(
        user_id=user_id,
        full_name=payload.full_name,
        age=payload.age,
        gender=payload.gender,
        height=payload.height,
        weight=payload.weight,
        activity_level=payload.activity_level,
        goal=payload.goal
    )

    result = await profiles_collection.insert_one(profile.model_dump(by_alias=True))
    return api_response(
        message="User profile created successfully",
        status=status.HTTP_201_CREATED,
        data={"profile_id": str(result.inserted_id)}
    )

@router.get("/user/profile")
async def get_user_profile(user_id: str = Depends(get_current_user_id)):
    if not user_id or not is_valid_object_id(user_id):
        return api_response("Invalid or missing user ID", status.HTTP_400_BAD_REQUEST)

    profile = await profiles_collection.find_one({"user_id": user_id})
    if not profile:
        return api_response("User profile not found", status.HTTP_404_NOT_FOUND)

    profile["_id"] = str(profile["_id"])
    return api_response(
        message="User profile fetched successfully",
        status=status.HTTP_200_OK,
        data=profile
    )

@router.patch("/user/profile")
async def update_user_profile(
    user_id: str = Depends(get_current_user_id),
    payload: UserProfileUpdate = Body(...)
):
    if not is_valid_object_id(user_id):
        return api_response("Invalid user ID", status.HTTP_400_BAD_REQUEST)

    profile = await profiles_collection.find_one({"user_id": user_id})
    if not profile:
        return api_response("User profile not found", status.HTTP_404_NOT_FOUND)

    update_data = {
        k: v for k, v in payload.model_dump(exclude_unset=True).items()
        if v is not None
    }

    if not update_data:
        return api_response("No valid fields to update", status.HTTP_400_BAD_REQUEST)

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
