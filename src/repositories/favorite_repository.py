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

    def get_user_favorite_place_ids(self, user_id: int) -> set[int]:
        """Returns a set of place_ids that the user has favorited."""
        results = self.session.query(Favorite.place_id)\
            .filter(Favorite.user_id == user_id).all()
        return {r[0] for r in results}

    def increment_place_favorite_count(self, place_id: int) -> None:
        """Atomically increment favorite_count on the place (race-condition safe)."""
        from src.models.place import Place
        self.session.query(Place).filter(Place.id == place_id).update(
            {Place.favorite_count: Place.favorite_count + 1},
            synchronize_session=False
        )

    def decrement_place_favorite_count(self, place_id: int) -> None:
        """Atomically decrement favorite_count on the place (floor at 0)."""
        from src.models.place import Place
        from sqlalchemy import case
        self.session.query(Place).filter(Place.id == place_id).update(
            {Place.favorite_count: case(
                (Place.favorite_count > 0, Place.favorite_count - 1),
                else_=0
            )},
            synchronize_session=False
        )
