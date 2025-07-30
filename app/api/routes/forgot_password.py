from fastapi import APIRouter, status, Form, HTTPException, Request
from jose import jwt, JWTError
from datetime import datetime , timezone
from app.utils.api_response import api_response
from app.utils.email import send_reset_email
from app.core.security import hash_password
from app.config.settings import settings
from app.db.mongodb import db
from app.schemas.forgot_password import ForgotPasswordRequest
from app.core.auth import create_reset_token

router = APIRouter()
users_collection = db["users"]
reset_requests_collection = db["password_reset_requests"]  # Optional: for rate limiting or audit



# ========================== #
#  FORGOT PASSWORD ENDPOINT  #
# ========================== #

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    user = await users_collection.find_one({"email": request.email})
    
    # Rate limiting: check last request timestamp (optional)
    if user and user.get("last_password_reset_at"):
        last_reset = user["last_password_reset_at"]
        if (datetime.now(timezone.utc) - last_reset).total_seconds() < 60:  # 60 sec limit
            return api_response(
                message="Please wait before requesting another reset.",
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

    if user:
        token = create_reset_token(user["email"])
        reset_link = f"http://localhost:8001/password?token={token}"
        send_reset_email(to_email=user["email"], reset_link=reset_link)

        # Store reset timestamp (optional)
        await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_password_reset_at": datetime.utcnow()}}
        )

    return api_response(
        message="If the email exists, a reset link has been sent.",
        status=status.HTTP_200_OK
    )

# ========================== #
#  RESET PASSWORD ENDPOINT   #
# ========================== #

@router.post("/reset-password")
async def reset_password(token: str = Form(...), new_password: str = Form(...)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:

            raise HTTPException(status_code=400, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await users_collection.update_one(
        {"email": email},
        {"$set": {"password_hash": hash_password(new_password)}}
    )

    return api_response(
        message="Password has been reset successfully.",
        status=status.HTTP_200_OK
    )
