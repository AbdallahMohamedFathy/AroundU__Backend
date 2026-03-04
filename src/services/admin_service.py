from src.core.unit_of_work import UnitOfWork
from src.core.permissions import require_admin
from src.schemas.user import UserResponse
from src.core.exceptions import APIException
from fastapi import status

def promote_user(uow: UnitOfWork, user_id: int, new_role: str, current_admin):
    """
    Promote or change a user's role. 
    Only admins can perform this action.
    """
    with uow:
        # 1. Permission check
        require_admin(current_admin)
        
        # 2. Prevent self-demotion or self-modification for safety
        if current_admin.id == user_id:
            raise APIException("You cannot change your own role", code=status.HTTP_400_BAD_REQUEST)
        
        # 3. Fetch user
        user = uow.user_repository.get_by_id(user_id)
        if not user:
            raise APIException("User not found", code=status.HTTP_404_NOT_FOUND)
        
        # 4. Validate role
        valid_roles = ["ADMIN", "USER"]
        if new_role.upper() not in valid_roles:
            raise APIException(f"Invalid role. Must be one of {valid_roles}. OWNER role is assigned automatically when creating a place.", code=status.HTTP_400_BAD_REQUEST)
        
        # 5. Apply change
        user.role = new_role.upper()
        uow.commit()
        
        return UserResponse.model_validate(user)
