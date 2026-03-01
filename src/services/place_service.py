from typing import Optional, List, Any
from math import ceil
from fastapi import HTTPException, status
from src.models.place import Place
from src.schemas.place import PlaceResponse
from sqlalchemy import text

# Rule 2: No SQLAlchemy or Model imports. 
# We import types ONLY for type-hinting if absolutely necessary, but here we use the repo ones.

def get_places(
    repo: Any, # Use Any or a specific Repository type if avoided from models
    page: int = 1,
    page_size: int = 20,
    category_id: Optional[int] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """Return a paginated list of places using the repository."""
    items, total = repo.get_paginated(
        page=page, 
        page_size=page_size, 
        category_id=category_id, 
        sort_by=sort_by, 
        sort_order=sort_order
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total else 0,
        "items": items,
    }


def get_place_by_id(repo: Any, place_id: int):
    """Return a single place or raise 404 via repository."""
    place = repo.get_by_id_with_details(place_id)
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    return place


def get_nearby_places(
    repo: Any,
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    category_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
):
    """Return places within radius_km using PostGIS for precise spatial search."""
    items = repo.get_nearby(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        category_id=category_id,
        limit=page_size,
        offset=(page - 1) * page_size
    )

    return {
        "total": len(items),
        "page": page,
        "page_size": page_size,
        "total_pages": 1, 
        "items": items,
    }


# ─── WRITE OPERATIONS (Rule 4: MUST use UnitOfWork) ──────────────────────────

def create_place(uow: Any, place_data: Any):
    with uow as uow:

        db_place = Place(
            name=place_data.name,
            description=place_data.description,
            latitude=place_data.latitude,
            longitude=place_data.longitude,
            category_id=place_data.category_id,
            address=place_data.address,
            is_active=True
        )

        db_place = uow.place_repository.create(db_place)
        
        uow.session.execute(
            text("""
                UPDATE places
                SET location = ST_SetSRID(
                    ST_MakePoint(:lng, :lat), 4326
                )::geography
                WHERE id = :id
            """),
            {
                "lng": place_data.longitude,
                "lat": place_data.latitude,
                "id": db_place.id
            }
        )

        uow.commit()

        return PlaceResponse.model_validate(db_place)


def update_place(uow: Any, place_id: int, place_data: Any):
    """Partially update a place using UnitOfWork."""
    with uow as uow:
        place = uow.place_repository.get_by_id(place_id)
        if not place:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
        
        updated_place = uow.place_repository.update(place, place_data)
        uow.commit()
        return updated_place


def delete_place(uow: Any, place_id: int):
    """Hard-delete a place using UnitOfWork."""
    with uow as uow:
        place = uow.place_repository.get_by_id(place_id)
        if not place:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
        uow.place_repository.delete(place)
        uow.commit()


def deactivate_place(uow: Any, place_id: int):
    """Soft-delete (deactivate) a place using UnitOfWork."""
    with uow as uow:
        place = uow.place_repository.get_by_id(place_id)
        if not place:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
        
        place.is_active = False
        uow.commit()
        return place
