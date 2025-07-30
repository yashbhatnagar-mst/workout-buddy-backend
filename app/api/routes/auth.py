
from fastapi import APIRouter, status , Depends , Response 
from fastapi.responses import JSONResponse
from app.schemas.auth import UserCreate , VerifyOTP , ResendOTP
from datetime import timezone,timedelta,datetime
from app.db.mongodb import db
from app.models.auth import User
from app.core.security import hash_password, verify_password
from app.core.auth import create_jwt_token
from app.utils.api_response import api_response
from fastapi.security import OAuth2PasswordRequestForm
import random
from app.utils.email import send_verification_email


router = APIRouter()
users_collection = db["users"]
otp_collection = db["otp_codes"]

@router.post("/register")
async def register_user(payload: UserCreate):
    # Check if user already exists
    if await users_collection.find_one({"email": payload.email}):
        return api_response(
            message="Email already registered",
            status=status.HTTP_409_CONFLICT
        )

    otp = str(random.randint(100000, 999999))  # 6-digit OTP

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        oauth_provider="local",
        is_verified=False
    )

    insert_result = await users_collection.insert_one(user.model_dump(by_alias=True))

    # Store OTP in a separate collection (recommended)
    await otp_collection.insert_one({
        "email": payload.email,
        "otp": otp,
        "created_at": datetime.now(timezone.utc), 
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)
    })

    # Send verification email
    # Send verification email
    send_verification_email(payload.email, otp)


    return api_response(
        message="User registered. Please verify your email.",
        status=status.HTTP_201_CREATED
    )

@router.post("/verify")
async def verify_account(data: VerifyOTP):
    record = await otp_collection.find_one({"email": data.email})

    if not record:
        return api_response(message="No OTP found for this email", status=404)

    # Update attempt count
    await otp_collection.update_one(
        {"_id": record["_id"]},
        {"$inc": {"attempts": 1}}
    )

    # Enforce retry limit
    if record.get("attempts", 0) >= 5:
        return api_response(message="Too many invalid attempts. Please request a new OTP.", status=429)

    # Check expiration
    expires_at = record["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        return api_response(message="OTP expired", status=400)

    if data.otp != record["otp"]:
        return api_response(message="Invalid OTP", status=400)

    # Success
    await users_collection.update_one({"email": data.email}, {"$set": {"is_verified": True}})
    await otp_collection.delete_one({"_id": record["_id"]})
    return api_response(message="Email verified successfully", status=200)



@router.post("/resend-otp")
async def resend_otp(data: ResendOTP):  # expects email in payload
    user = await users_collection.find_one({"email": data.email})
    if not user:
        api_response("User not found" , status.HTTP_404_NOT_FOUND)

    if user.get("is_verified"):
        return api_response(message="User already verified", status=400)

    # Rate limit check
    recent_otp = await otp_collection.find_one({"email": data.email})
    if recent_otp:
        created_at = recent_otp["created_at"]
        print(created_at)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    if (datetime.now(timezone.utc) - created_at).seconds < 60:

            return api_response(message="Please wait 60 seconds before resending OTP", status=429)

    # Generate and store new OTP
    otp = str(random.randint(100000, 999999))
    await otp_collection.update_one(
        {"email": data.email},
        {"$set": {
            "otp": otp,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
            "attempts": 0  # Reset attempt count
        }},
        upsert=True
    )

    send_verification_email(data.email, otp)
    return api_response(message="OTP resent successfully", status=200)


@router.post("/login")
async def login_user(payload: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection.find_one({"email": payload.username})
    
    if not user or not verify_password(payload.password, user["password_hash"]):
        return JSONResponse(
            content={"message": "Invalid email or password"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    if not user.get("is_verified", False):
        return JSONResponse(
            content={"message": "Account not verified. Please check your email for the OTP."},
            status_code=status.HTTP_403_FORBIDDEN
        )

    token = create_jwt_token(user_id=str(user["_id"]), email=user["email"])
    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout_user(response: Response):
    response.delete_cookie(key="access_token")
    return api_response(
        message="User logged out successfully",
        status=status.HTTP_200_OK
    )