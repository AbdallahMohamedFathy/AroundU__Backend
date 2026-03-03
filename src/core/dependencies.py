from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.config import settings
from src.core.database import SessionLocal, get_db
from src.core.unit_of_work import UnitOfWork
def get_uow():
    with UnitOfWork(SessionLocal) as uow:
        yield uow
from src.core.exceptions import APIException
from src.core.unit_of_work import UnitOfWork

from src.repositories.user_repository import UserRepository
from src.repositories.place_repository import PlaceRepository
from src.repositories.review_repository import ReviewRepository
from src.repositories.favorite_repository import FavoriteRepository
from src.repositories.category_repository import CategoryRepository
from src.repositories.place_image_repository import PlaceImageRepository
from src.repositories.chat_message_repository import ChatMessageRepository
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.search_repository import SearchRepository

from src.schemas.user import UserResponse
from src.services import user_service


# =========================================================
# Rate Limiter
# =========================================================

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL if settings.ENABLE_REDIS else "memory://"
)


# =========================================================
# Repository Providers (IMPORTANT: DEFINE FIRST)
# =========================================================

def get_user_repository(db: Session = Depends(get_db)):
    return UserRepository(db)


def get_place_repository(db: Session = Depends(get_db)):
    return PlaceRepository(db)


def get_review_repository(db: Session = Depends(get_db)):
    return ReviewRepository(db)


def get_favorite_repository(db: Session = Depends(get_db)):
    return FavoriteRepository(db)


def get_category_repository(db: Session = Depends(get_db)):
    return CategoryRepository(db)


def get_place_image_repository(db: Session = Depends(get_db)):
    return PlaceImageRepository(db)


def get_chat_message_repository(db: Session = Depends(get_db)):
    return ChatMessageRepository(db)


def get_conversation_repository(db: Session = Depends(get_db)):
    return ConversationRepository(db)


def get_message_repository(db: Session = Depends(get_db)):
    return MessageRepository(db)


def get_search_repository(db: Session = Depends(get_db)):
    return SearchRepository(db)

# provider for unit of work
def get_uow():
    with UnitOfWork(SessionLocal) as uow:
        yield uow

# =========================================================
# OAuth2
# =========================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/mobile/auth/login"
)


# =========================================================
# Current User Dependency
# =========================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    repo: UserRepository = Depends(get_user_repository)
) -> UserResponse:

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        if payload.get("type") != "access":
            raise APIException(
                "Invalid token type",
                code=status.HTTP_401_UNAUTHORIZED
            )

        user_id = payload.get("sub")

        if not user_id:
            raise APIException(
                "Invalid token payload",
                code=status.HTTP_401_UNAUTHORIZED
            )

    except jwt.PyJWTError:
        raise APIException(
            "Invalid credentials",
            code=status.HTTP_401_UNAUTHORIZED
        )

    user = user_service.get_user_by_id(repo, int(user_id))

    if not user or not user.is_active:
        raise APIException(
            "Account is inactive",
            code=status.HTTP_403_FORBIDDEN
        )

    return user


# =========================================================
# Role Checker
# =========================================================

class RoleChecker:

    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, user: UserResponse = Depends(get_current_user)):

        role = str(user.role)

        if role not in self.allowed_roles:
            raise APIException(
                f"Role '{role}' not allowed",
                code=status.HTTP_403_FORBIDDEN
            )

        return user