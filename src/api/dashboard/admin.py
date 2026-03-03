from fastapi import APIRouter, Depends
from src.core.dependencies import get_uow, get_current_user
from src.schemas.user import UserResponse
from src.schemas.admin import UserPromotion
from src.services import admin_service
from src.core.permissions import require_admin

router = APIRouter(dependencies=[Depends(get_current_user), Depends(require_admin)])

@router.post("/promote/{user_id}", response_model=UserResponse)
def promote_user(
    user_id: int,
    promotion: UserPromotion,
    uow=Depends(get_uow),
    current_user=Depends(get_current_user)
):
    """
    Change a user's role. Requires ADMIN privilege.
    """
    return admin_service.promote_user(uow, user_id, promotion.role, current_user)
