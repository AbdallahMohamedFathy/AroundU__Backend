from typing import Optional, List, Any
from math import ceil
from datetime import datetime, timezone
from fastapi import HTTPException, status
from src.models.place import Place
from src.schemas.place import PlaceResponse
from src.services.location_parser import extract_coordinates_from_google_maps
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


from src.core.permissions import require_place_owner_or_admin, require_admin

# ─── WRITE OPERATIONS (Rule 4: MUST use UnitOfWork) ──────────────────────────

from src.core.exceptions import APIException

def create_place(uow: Any, request_data: Any, current_user: Any):
    # Only ADMIN can create places in this new architecture
    require_admin(current_user)
    
    with uow as uow:
        # 1. Fetch the target owner
        target_user = uow.user_repository.get_by_id(request_data.owner_user_id)
        if not target_user:
            raise APIException("Target owner not found", code=status.HTTP_404_NOT_FOUND)
            
        # 2. Ensure target is a standard USER
        if target_user.role != "USER":
            raise APIException("Place must be assigned to a standard USER account", code=status.HTTP_400_BAD_REQUEST)
            
        # 3. Prevent duplicate ownership
        existing_place = uow.place_repository.get_by_owner_id(request_data.owner_user_id)
        if existing_place:
            raise APIException("User already owns a place", code=status.HTTP_400_BAD_REQUEST)
            
        # 4. Promote target user to OWNER
        target_user.role = "OWNER"

        # 5. Create Place
        db_place = Place(
            **request_data.place_data.model_dump(),
            owner_id=target_user.id,
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
                "lng": request_data.place_data.longitude,
                "lat": request_data.place_data.latitude,
                "id": db_place.id
            }
        )

        uow.commit()

        return PlaceResponse.model_validate(db_place)


def update_place(uow: Any, place_id: int, place_data: Any, current_user: Any):

    with uow as uow:

        place = uow.place_repository.get_by_id(place_id)

        if not place:
            raise HTTPException(status_code=404, detail="Place not found")

        require_place_owner_or_admin(current_user, place)

        update_data = place_data.model_dump(exclude_unset=True)

        # Handle Google Maps link
        if "location_link" in update_data:

            lat, lng = extract_coordinates_from_google_maps(update_data["location_link"])

            place.latitude = lat
            place.longitude = lng

            del update_data["location_link"]

        updated_place = uow.place_repository.update(place, update_data)

        # Update PostGIS location
        uow.session.execute(
            text("""
                UPDATE places
                SET location = ST_SetSRID(
                    ST_MakePoint(longitude, latitude), 4326
                )::geography
                WHERE id = :id
            """),
            {"id": place_id}
        )

        uow.commit()

        return updated_place


def delete_place(uow: Any, place_id: int, current_user: Any):
    """Hard-delete a place using UnitOfWork."""
    with uow as uow:
        place = uow.place_repository.get_by_id(place_id)
        if not place:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
        
        # Permission check
        require_place_owner_or_admin(current_user, place)
        
        uow.place_repository.delete(place)
        uow.commit()


def deactivate_place(uow: Any, place_id: int, current_user: Any):
    """Soft-delete (deactivate) a place using UnitOfWork."""
    with uow as uow:
        place = uow.place_repository.get_by_id(place_id)
        if not place:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
        
        # Permission check
        require_place_owner_or_admin(current_user, place)
        
        place.is_active = False
        uow.commit()
        return place
