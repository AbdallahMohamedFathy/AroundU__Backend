from typing import List, Optional
from src.core.unit_of_work import UnitOfWork
from src.repositories.favorite_repository import FavoriteRepository
from src.schemas.favorite import FavoriteCreate
from src.core.exceptions import APIException
from fastapi import status


def add_favorite(uow: UnitOfWork, user_id: int, favorite_data: FavoriteCreate):
    with uow:
        # Check if place exists
        place = uow.place_repository.get_by_id(favorite_data.place_id)
        if not place:
            raise APIException("Place not found", code=status.HTTP_404_NOT_FOUND)

        # Check if already favorited
        existing = uow.favorite_repository.get_by_user_and_place(user_id, favorite_data.place_id)
        if existing:
            raise APIException("Place already in favorites", code=status.HTTP_400_BAD_REQUEST)

        # Create favorite
        from src.models.favorite import Favorite
        new_favorite = Favorite(user_id=user_id, place_id=favorite_data.place_id)
        uow.favorite_repository.create(new_favorite)

        # Atomically increment favorite_count on the place
        uow.favorite_repository.increment_place_favorite_count(favorite_data.place_id)

        uow.commit()
        return new_favorite


def get_user_favorites(repo: FavoriteRepository, user_id: int):
    """Get all favorites for a user with place details."""
    return repo.get_user_favorites(user_id)


def remove_favorite(uow: UnitOfWork, user_id: int, place_id: int) -> bool:
    with uow:
        favorite = uow.favorite_repository.get_by_user_and_place(user_id, place_id)
        if not favorite:
            raise APIException("Favorite not found", code=status.HTTP_404_NOT_FOUND)

        uow.favorite_repository.delete(favorite)

        # Atomically decrement favorite_count on the place
        uow.favorite_repository.decrement_place_favorite_count(place_id)

        uow.commit()
        return True


def is_favorited(repo: FavoriteRepository, user_id: int, place_id: int) -> bool:
    favorite = repo.get_by_user_and_place(user_id, place_id)
    return favorite is not None
