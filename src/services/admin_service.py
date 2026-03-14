from src.core.unit_of_work import UnitOfWork
from src.core.permissions import require_admin
from src.schemas.user import UserResponse
from src.core.exceptions import APIException
from fastapi import status
from src.core.security import get_password_hash
from src.models.user import User
from src.models.place import Place
from src.schemas.admin import PlaceCreationResponse
from src.services.location_parser import extract_coordinates_from_google_maps
from sqlalchemy import text

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

def create_place_with_owner(uow: UnitOfWork, place_in, current_admin):
    """
    Business flow: Create an owner user, then create a place linked to that user.
    """
    with uow:
        # 1. Admin permission check
        require_admin(current_admin)

        # 2. Check if owner email already exists
        existing_user = uow.user_repository.get_by_email(place_in.owner_email)
        if existing_user:
            raise APIException("A user with this email already exists", code=status.HTTP_400_BAD_REQUEST)

        # 3. Create the Owner user
        new_owner = User(
            full_name=f"Owner of {place_in.place_name}",
            email=place_in.owner_email,
            password_hash=get_password_hash(place_in.owner_password),
            role="OWNER",
            is_active=True,
            is_verified=True
        )
        uow.user_repository.create(new_owner)
        
        # 4. Handle Location Parsing
        lat = place_in.latitude
        lng = place_in.longitude
        
        if place_in.location_link:
            lat, lng = extract_coordinates_from_google_maps(place_in.location_link)

        if lat is None or lng is None:
            raise APIException("Latitude and Longitude are required if location_link is not provided", code=status.HTTP_400_BAD_REQUEST)

        # 5. Create the Place
        new_place = Place(
            name=place_in.place_name,
            description=place_in.description,
            category_id=place_in.category_id,
            latitude=lat,
            longitude=lng,
            owner_id=new_owner.id,
            is_active=True
        )
        new_place = uow.place_repository.create(new_place)

        # 6. Update PostGIS location
        uow.session.execute(
            text("""
                UPDATE places
                SET location = ST_SetSRID(
                    ST_MakePoint(:lng, :lat), 4326
                )::geography
                WHERE id = :id
            """),
            {
                "lng": lng,
                "lat": lat,
                "id": new_place.id
            }
        )

        uow.commit()

        return PlaceCreationResponse(
            place_id=new_place.id,
            owner_id=new_owner.id,
            owner_email=new_owner.email
        )
