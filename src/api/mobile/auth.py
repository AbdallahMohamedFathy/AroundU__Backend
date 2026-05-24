import jwt
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from src.core.dependencies import get_user_repository, get_uow, get_current_user, RoleChecker, limiter
from src.core.config import settings
from src.schemas.user import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    PasswordChange, PasswordResetRequest, PasswordReset, AuthResponse
)
from src.services import auth_service, user_service
from src.core.exceptions import APIException

router = APIRouter()

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# ─── REGISTER  POST /auth/register ──────────────────────────────────────────
@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=AuthResponse)
@limiter.limit("5/minute")
def register(request: Request, user_in: UserCreate, uow=Depends(get_uow)):
    """Create a new user account and return access + refresh tokens."""
    return auth_service.register_user(uow, user_in)


# ─── LOGIN  POST /auth/login ─────────────────────────────────────────────────
@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), uow=Depends(get_uow)):
    """Authenticate and return access + refresh tokens."""
    user_in = UserLogin(email=form_data.username, password=form_data.password)
    return auth_service.authenticate_user(uow, user_in)


# ─── SOCIAL LOGIN  POST /auth/social-login ───────────────────────────────────
from src.schemas.user import SocialLogin

@router.post("/social-login", response_model=AuthResponse)
@limiter.limit("5/minute")
def social_login(request: Request, data: SocialLogin, uow=Depends(get_uow)):
    """Authenticate or Register a user using Firebase ID Token (Google/Apple)."""
    return auth_service.social_login(uow, data)

# ─── REFRESH  POST /auth/refresh-token ──────────────────────────────────────
@router.post("/refresh-token")
def refresh_token(body: RefreshTokenRequest, uow=Depends(get_uow)):
    """Issue a new access token using a valid refresh token (pass token in request body)."""
    token = body.refresh_token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise APIException("Invalid token type", code=status.HTTP_401_UNAUTHORIZED)
        user_id = payload.get("sub")
    except jwt.PyJWTError:
        raise APIException("Invalid refresh token", code=status.HTTP_401_UNAUTHORIZED)

    return auth_service.refresh_access_token(uow, user_id, token)


# ─── GET PROFILE  GET /auth/profile ─────────────────────────────────────────
@router.get("/profile", response_model=UserResponse)
def get_profile(current_user=Depends(get_current_user)):
    """Return the current user's profile."""
    return current_user


# ─── UPDATE PROFILE  PUT /auth/profile ──────────────────────────────────────
@router.put("/profile", response_model=UserResponse)
def update_profile(
    data: UserUpdate,
    uow=Depends(get_uow),
    current_user=Depends(get_current_user),
):
    """Update the current user's name or email."""
    return user_service.update_user_profile(uow, current_user.id, data)


# ─── CHANGE PASSWORD  POST /auth/change-password ────────────────────────────
@router.post("/change-password")
def change_my_password(
    data: PasswordChange,
    uow=Depends(get_uow),
    current_user=Depends(get_current_user),
):
    """Change password (requires current password)."""
    user_service.change_password(uow, current_user.id, data.current_password, data.new_password)
    return {"message": "Password changed successfully"}


# ─── VERIFY EMAIL  GET /auth/verify-email ───────────────────────────────────
@router.get("/verify-email")
def verify_user_email(token: str, uow=Depends(get_uow)):
    """Verify a user's email address using the token sent by email."""
    auth_service.verify_email(uow, token)
    return {"message": "Email verified successfully"}


from fastapi import BackgroundTasks

# ─── FORGOT PASSWORD  POST /auth/forgot-password ────────────────────────────
@router.post("/forgot-password")
@limiter.limit("5/minute")
def forgot_password(request: Request, data: PasswordResetRequest, background_tasks: BackgroundTasks, uow=Depends(get_uow)):
    """Send a password-reset link to the provided email (if it exists)."""
    auth_service.request_password_reset(uow, data.email, background_tasks)
    return {"message": "If that email is registered, a reset link has been sent"}


# ─── RESET PASSWORD  POST /auth/reset-password ──────────────────────────────
@router.post("/reset-password")
def do_reset_password(data: PasswordReset, uow=Depends(get_uow)):
    """Reset password using the token received by email."""
    auth_service.reset_password(uow, data.token, data.new_password)
    return {"message": "Password reset successfully. Please log in."}

