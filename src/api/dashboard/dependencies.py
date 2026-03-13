from fastapi import Depends, HTTPException, status
from src.core.dependencies import get_current_user
from src.models.user import User
from src.core.permissions import require_admin, require_dashboard_access

def dashboard_guard(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency that ensures the user has dashboard access (ADMIN or OWNER).
    Returns the current user if authorized.
    """
    require_dashboard_access(current_user)
    return current_user

def admin_guard(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency that ensures the user is an ADMIN.
    Returns the current user if authorized.
    """
    require_admin(current_user)
    return current_user

def owner_guard(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required"
        )
    return current_user
