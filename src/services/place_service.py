from typing import Optional, List, Any
from math import ceil
from datetime import datetime, timezone
from fastapi import HTTPException, status
from src.models.place import Place
from src.schemas.place import PlaceResponse
from src.services.location_parser import extract_coordinates_from_google_maps
from sqlalchemy import text
from src.core.exceptions import APIException
from src.core.logger import logger

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
    """Partially update a place using UnitOfWork."""
    with uow as uow:
        try:
            place = uow.place_repository.get_by_id(place_id)
            if not place:
                raise APIException("Place not found", code=status.HTTP_404_NOT_FOUND)

            require_place_owner_or_admin(current_user, place)

            # Convert schema to dict
            update_data = place_data.model_dump(exclude_unset=True)

            # Handle Google Maps link parsing
            loc_link = update_data.get("location_link")
            if loc_link and loc_link.strip():
                try:
                    lat, lng = extract_coordinates_from_google_maps(loc_link)
                    if lat is not None and lng is not None:
                        place.latitude = lat
                        place.longitude = lng
                        # Avoid overwriting link-extracted coords with potentially stale raw values
                        update_data.pop("latitude", None)
                        update_data.pop("longitude", None)
                except ValueError as e:
                    raise APIException(str(e), code=status.HTTP_400_BAD_REQUEST)
                
                update_data.pop("location_link", None)

            # Perform the update
            updated_place = uow.place_repository.update(place, update_data)

            # 4. Refresh PostGIS location with explicit parameters
            uow.session.execute(
                text("""
                    UPDATE places
                    SET location = ST_SetSRID(
                        ST_MakePoint(:lng, :lat), 4326
                    )::geography
                    WHERE id = :id
                """),
                {
                    "lng": place.longitude,
                    "lat": place.latitude,
                    "id": place_id
                }
            )

            # Load primary relationships before commit to avoid DetachedInstanceError
            # Pydantic serialization will trigger these loads
            response_data = PlaceResponse.model_validate(updated_place)

            uow.commit()
            return response_data
            
        except APIException:
            raise
        except Exception as e:
            import traceback
            logger.error(f"Place update failed: {traceback.format_exc()}")
            raise APIException(f"Update failed: {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
