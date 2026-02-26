from fastapi import Depends, Request, status
import jwt
from src.core.config import settings
from src.core.exceptions import APIException
from src.schemas.user import UserResponse
from src.services import user_service
from fastapi.security import OAuth2PasswordBearer
from slowapi import Limiter
from slowapi.util import get_remote_address

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Rate Limiter Initialization
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL if settings.ENABLE_REDIS else "memory://"
)

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    repo=Depends(get_user_repository)
):
    """Strict JWT verification (Access tokens only)."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise APIException("Invalid token type", code=status.HTTP_401_UNAUTHORIZED)
        user_id = payload.get("sub")
    except jwt.PyJWTError:
        raise APIException("Invalid credentials", code=status.HTTP_401_UNAUTHORIZED)

    user = user_service.get_user_by_id(repo, int(user_id))
    if not user.is_active:
        raise APIException("Account is deactivated", code=status.HTTP_403_FORBIDDEN)
    return user

class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, user: UserResponse = Depends(get_current_user)):
        user_role = user.role.value if hasattr(user.role, "value") else str(user.role)
        if user_role not in self.allowed_roles:
            raise APIException(
                f"Role '{user_role}' is not allowed", 
                code=status.HTTP_403_FORBIDDEN
            )
        return user
from src.core.database import get_db
from src.core.unit_of_work import UnitOfWork
from src.repositories.user_repository import UserRepository
from src.repositories.place_repository import PlaceRepository
from src.repositories.review_repository import ReviewRepository
from src.repositories.favorite_repository import FavoriteRepository

def get_uow():
    """Provider for UnitOfWork to manage atomic transactions."""
    with UnitOfWork() as uow:
        yield uow

def get_user_repository(session: Session = Depends(get_db)):
    """Provider for UserRepository."""
    return UserRepository(session)

def get_place_repository(session: Session = Depends(get_db)):
    """Provider for PlaceRepository."""
    return PlaceRepository(session)

def get_review_repository(session: Session = Depends(get_db)):
    """Provider for ReviewRepository."""
    return ReviewRepository(session)

def get_favorite_repository(db: Session = Depends(get_db)):
    from src.repositories.favorite_repository import FavoriteRepository
    return FavoriteRepository(db)

def get_category_repository(db: Session = Depends(get_db)):
    from src.repositories.category_repository import CategoryRepository
    return CategoryRepository(db)

def get_place_image_repository(db: Session = Depends(get_db)):
    from src.repositories.place_image_repository import PlaceImageRepository
    return PlaceImageRepository(db)

def get_chat_message_repository(db: Session = Depends(get_db)):
    from src.repositories.chat_message_repository import ChatMessageRepository
    return ChatMessageRepository(db)

def get_conversation_repository(db: Session = Depends(get_db)):
    from src.repositories.conversation_repository import ConversationRepository
    return ConversationRepository(db)

def get_message_repository(db: Session = Depends(get_db)):
    from src.repositories.message_repository import MessageRepository
    return MessageRepository(db)

def get_search_repository(db: Session = Depends(get_db)):
    from src.repositories.search_repository import SearchRepository
    return SearchRepository(db)
