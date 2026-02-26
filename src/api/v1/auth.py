import jwt
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from src.core.dependencies import get_user_repository, get_uow, get_current_user, RoleChecker, limiter
from src.core.config import settings
from src.schemas.user import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    PasswordChange, PasswordResetRequest, PasswordReset, AuthResponse
)
from src.services import auth_service, user_service
from src.core.exceptions import APIException

router = APIRouter()

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


# ─── REFRESH  POST /auth/refresh-token ──────────────────────────────────────
@router.post("/refresh-token")
def refresh_token(refresh_token: str, uow=Depends(get_uow)):
    """Issuer a new access token using a valid refresh token."""
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise APIException("Invalid token type", code=status.HTTP_401_UNAUTHORIZED)
        user_id = payload.get("sub")
    except jwt.PyJWTError:
        raise APIException("Invalid refresh token", code=status.HTTP_401_UNAUTHORIZED)
    
    # Must use service to check the refresh token hash against DB
    return auth_service.refresh_access_token(uow, user_id, refresh_token)


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


# ─── FORGOT PASSWORD  POST /auth/forgot-password ────────────────────────────
@router.post("/forgot-password")
def forgot_password(data: PasswordResetRequest, uow=Depends(get_uow)):
    """Send a password-reset link to the provided email (if it exists)."""
    auth_service.request_password_reset(uow, data.email)
    return {"message": "If that email is registered, a reset link has been sent"}


# ─── RESET PASSWORD  POST /auth/reset-password ──────────────────────────────
@router.post("/reset-password")
def do_reset_password(data: PasswordReset, uow=Depends(get_uow)):
    """Reset password using the token received by email."""
    auth_service.reset_password(uow, data.token, data.new_password)
    return {"message": "Password reset successfully. Please log in."}

