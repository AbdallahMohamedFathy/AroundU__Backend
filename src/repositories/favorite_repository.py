from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from src.models.favorite import Favorite
from src.repositories.base_repository import BaseRepository

class FavoriteRepository(BaseRepository[Favorite]):
    """Repository for Favorite model."""
    
    def __init__(self, session: Session):
        super().__init__(Favorite, session)

    def get_user_favorites(self, user_id: int, limit: int = 20, offset: int = 0) -> List[Favorite]:
        return self.session.query(Favorite)\
            .options(joinedload(Favorite.place))\
            .filter(Favorite.user_id == user_id)\
            .offset(offset).limit(limit).all()

    def get_by_user_and_place(self, user_id: int, place_id: int) -> Optional[Favorite]:
        return self.session.query(Favorite)\
            .filter(Favorite.user_id == user_id, Favorite.place_id == place_id)\
            .first()
