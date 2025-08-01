from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from app.config.settings import settings
from app.db.mongodb import db
from app.core.auth import create_jwt_token
from app.models.auth import User


router = APIRouter()

# Register Google OAuth provider
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@router.get("/google/login")
async def login_via_google(request: Request):
    redirect_uri = request.url_for("google_auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback", name="google_auth_callback")
async def google_auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = await oauth.google.userinfo(token=token)

    email = user_info["email"]
    users_collection = db["users"]

    # Check if user exists
    user = await users_collection.find_one({"email": email})
    if not user:
        new_user = User(
            email=email,
            password_hash="",  # No password for OAuth users
            oauth_provider="google",
            is_verified=True
        )
        insert_result = await users_collection.insert_one(new_user.model_dump(by_alias=True))
        user_id = str(insert_result.inserted_id)
    else:
        user_id = str(user["_id"])
 
    # ✅ FIXED: Create JWT using expected parameters
    jwt_token = create_jwt_token(user_id=user_id, email=email)

    redirect_url = f"https://workoutbuddy-frontend-r4f7.onrender.com/login/callback?token={jwt_token}"
    return RedirectResponse(url=redirect_url)