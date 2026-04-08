from typing import List, Dict
from src.core.unit_of_work import UnitOfWork
from src.core.permissions import require_admin
from src.schemas.user import UserResponse
from src.core.exceptions import APIException
from fastapi import status
from src.core.security import get_password_hash
from src.models.user import User
from src.models.place import Place
from src.models.property import Property
from src.models.property_image import PropertyImage
from src.models.interaction import Interaction
from src.models.review import Review
from src.models.favorite import Favorite
from src.models.chat_message import ChatMessage
from src.models.category import Category
from src.schemas.admin import PlaceCreationResponse, PropertyCreationResponse, PlatformStats, TrendingDay, PlaceStats, UserStats
from src.utils.location_parser import extract_coordinates
from sqlalchemy import text, func, case, inspect
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)

# --- Database Management Logic (Generic CRUD) ---

def get_db_tables(uow: UnitOfWork, current_admin):
    """List all table names in the database."""
    require_admin(current_admin)
    with uow:
        inspector = inspect(uow.session.bind)
        return inspector.get_table_names()

def get_table_data(uow: UnitOfWork, table_name: str, current_admin):
    """Fetch all rows and columns for a specific table."""
    require_admin(current_admin)
    with uow:
        # Check if table exists to prevent SQL injection
        inspector = inspect(uow.session.bind)
        if table_name not in inspector.get_table_names():
            raise APIException(f"Table '{table_name}' not found", code=status.HTTP_404_NOT_FOUND)
            
        columns = [c["name"] for c in inspector.get_columns(table_name)]
        query = text(f"SELECT * FROM {table_name}")
        rows = uow.session.execute(query).mappings().all()
        
        # Convert rows to dicts, handling non-serializable types
        data = []
        for row in rows:
            r_dict = {}
            for k, v in row.items():
                if isinstance(v, (datetime, date)):
                    r_dict[k] = v.isoformat()
                elif hasattr(v, "__str__") and "ST_" in str(type(v)): # Geo types
                    r_dict[k] = "Geo Data"
                else:
                    r_dict[k] = v
            data.append(r_dict)
            
        return {"columns": columns, "data": data}

def execute_db_operation(uow: UnitOfWork, table_name: str, operation: str, data: dict, row_id: int, current_admin):
    """Perform Insert, Update, or Delete on any table."""
    require_admin(current_admin)
    with uow:
        inspector = inspect(uow.session.bind)
        if table_name not in inspector.get_table_names():
            raise APIException(f"Table '{table_name}' not found", code=status.HTTP_404_NOT_FOUND)

        if operation == "DELETE":
            query = text(f"DELETE FROM {table_name} WHERE id = :id")
            uow.session.execute(query, {"id": row_id})
        
        elif operation == "UPDATE":
            if not data: return
            cols_str = ", ".join([f"{k} = :{k}" for k in data.keys() if k != "id"])
            query = text(f"UPDATE {table_name} SET {cols_str} WHERE id = :id")
            data["id"] = row_id
            uow.session.execute(query, data)
            
        elif operation == "INSERT":
            if not data: return
            cols = ", ".join(data.keys())
            placeholders = ", ".join([f":{k}" for k in data.keys()])
            query = text(f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})")
            uow.session.execute(query, data)
            
        uow.commit()
        return {"status": "success", "message": f"{operation} successful on {table_name}"}

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
            try:
                coords = extract_coordinates(place_in.location_link)
                if coords:
                    lat, lng = coords
            except Exception as e:
                logger.error(f"Admin create place: Location parsing failed: {str(e)}")

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

def create_property_with_owner(uow: UnitOfWork, property_in, current_admin):
    """
    Business flow: Create an owner user, then create a property linked to that user.
    """
    with uow:
        # 1. Admin permission check
        require_admin(current_admin)

        # 2. Check if owner email already exists
        existing_user = uow.user_repository.get_by_email(property_in.owner_email)
        if existing_user:
            raise APIException("A user with this email already exists", code=status.HTTP_400_BAD_REQUEST)

        # 3. Create the Owner user
        new_owner = User(
            full_name=f"Owner of {property_in.title}",
            email=property_in.owner_email,
            password_hash=get_password_hash(property_in.owner_password),
            role="OWNER",
            is_active=True,
            is_verified=True
        )
        uow.user_repository.create(new_owner)
        
        # 4. Handle Location Parsing
        lat = property_in.latitude
        lng = property_in.longitude

        if property_in.location_link:
            try:
                coords = extract_coordinates(property_in.location_link)
                if coords:
                    lat, lng = coords
            except Exception as e:
                pass

        if lat is None or lng is None:
            raise APIException("Latitude and Longitude are required if location_link is not provided", code=status.HTTP_400_BAD_REQUEST)

        # 5. Create the Property
        new_property = Property(
            title=property_in.title,
            description=property_in.description,
            price=property_in.price,
            latitude=lat,
            longitude=lng,
            owner_id=new_owner.id,
            is_available=True
        )
        new_property = uow.property_repository.create(new_property)

        uow.commit()

        return PropertyCreationResponse(
            property_id=new_property.id,
            owner_id=new_owner.id,
            owner_email=new_owner.email
        )


from fastapi import UploadFile
from src.services.cloudinary_service import upload_image

MAX_PROPERTY_IMAGES = 5

def upload_property_images(uow, property_id: int, images: list, current_admin):
    """
    Upload images for an existing property. Admin only.
    """
    with uow:
        require_admin(current_admin)

        prop = uow.property_repository.get_by_id_with_images(property_id)
        if not prop:
            raise APIException("Property not found", code=status.HTTP_404_NOT_FOUND)

        current_count = len(prop.images)
        if current_count + len(images) > MAX_PROPERTY_IMAGES:
            raise APIException(
                f"Cannot upload {len(images)} images. Property already has {current_count} images. Max allowed: {MAX_PROPERTY_IMAGES}",
                code=status.HTTP_400_BAD_REQUEST
            )

        uploaded_urls = []
        for image in images:
            url = upload_image(image, folder="properties")
            new_img = PropertyImage(property_id=prop.id, image_url=url)
            uow.session.add(new_img)
            uploaded_urls.append(url)

            # Set first image as main_image_url if not already set
            if not prop.main_image_url:
                prop.main_image_url = url

        uow.commit()

        return {
            "property_id": property_id,
            "uploaded": len(uploaded_urls),
            "urls": uploaded_urls
        }

# --- Statistics & Dashboard Logic ---

def get_platform_stats(uow: UnitOfWork, start_date: date = None, end_date: date = None) -> PlatformStats:
    """
    Get high-level statistics for the entire platform.
    """
    with uow:
        # Defaults
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        # 1. Total Visits
        visits = uow.session.query(func.count(Interaction.id)).filter(
            Interaction.type == "visit",
            func.date(Interaction.created_at) >= start_date,
            func.date(Interaction.created_at) <= end_date
        ).scalar() or 0
        
        # 2. New Users
        new_users = uow.session.query(func.count(User.id)).filter(
            User.role == "USER",
            func.date(User.created_at) >= start_date,
            func.date(User.created_at) <= end_date
        ).scalar() or 0
        
        # 3. New Owners
        new_owners = uow.session.query(func.count(User.id)).filter(
            User.role == "OWNER",
            func.date(User.created_at) >= start_date,
            func.date(User.created_at) <= end_date
        ).scalar() or 0
        
        # 4. Total Saves (Favorites)
        saves = uow.session.query(func.count(Favorite.id)).filter(
            func.date(Favorite.created_at) >= start_date,
            func.date(Favorite.created_at) <= end_date
        ).scalar() or 0
        
        # 5. Interaction Types
        interactions = uow.session.query(
            Interaction.type, func.count(Interaction.id)
        ).filter(
            func.date(Interaction.created_at) >= start_date,
            func.date(Interaction.created_at) <= end_date
        ).group_by(Interaction.type).all()
        
        directions = 0
        calls = 0
        for itype, count in interactions:
            if itype == "direction": directions = count
            elif itype == "call": calls = count
            
        # 6. Reviews
        reviews = uow.session.query(func.count(Review.id)).filter(
            func.date(Review.created_at) >= start_date,
            func.date(Review.created_at) <= end_date
        ).scalar() or 0
        
        # 7. Chats
        chats = uow.session.query(func.count(ChatMessage.id)).filter(
            func.date(ChatMessage.created_at) >= start_date,
            func.date(ChatMessage.created_at) <= end_date
        ).scalar() or 0
        
        # 8. Active Places
        active_places = uow.session.query(func.count(Place.id)).filter(Place.is_active == True).scalar() or 0
        
        # Calculate Deltas (compared to previous period of same length)
        days_diff = (end_date - start_date).days + 1
        prev_start = start_date - timedelta(days=days_diff)
        prev_end = start_date - timedelta(days=1)
        
        def calculate_delta(curr_val, model, filters=None, date_field="created_at"):
            query = uow.session.query(func.count(model.id))
            if filters is not None:
                query = query.filter(*filters)
            prev_val = query.filter(
                func.date(getattr(model, date_field)) >= prev_start,
                func.date(getattr(model, date_field)) <= prev_end
            ).scalar() or 0
            if prev_val == 0: return "+100%" if curr_val > 0 else "0%"
            pct = int(((curr_val - prev_val) / prev_val) * 100)
            return f"{pct:+}%"

        # Special visits delta (type check)
        prev_visits = uow.session.query(func.count(Interaction.id)).filter(
            Interaction.type == "visit",
            func.date(Interaction.created_at) >= prev_start,
            func.date(Interaction.created_at) <= prev_end
        ).scalar() or 0
        visits_delta = f"{int(((visits - prev_visits) / prev_visits * 100)) if prev_visits > 0 else 0:+}%"

        return PlatformStats(
            visits=visits,
            new_users=new_users,
            new_owners=new_owners,
            saves=saves,
            directions=directions,
            calls=calls,
            reviews=reviews,
            chats=chats,
            resolved_chats=int(chats * 0.9), # Mocking resolution for now
            active_places=active_places,
            visits_delta=visits_delta,
            users_delta=calculate_delta(new_users, User, [User.role == "USER"]),
            saves_delta=calculate_delta(saves, Favorite),
            directions_delta="0%", # complex to calculate precisely across types here
            calls_delta="0%",
            reviews_delta=calculate_delta(reviews, Review)
        )

def get_platform_trending(uow: UnitOfWork, start_date: date = None, end_date: date = None) -> List[TrendingDay]:
    """
    Get daily trends for the platform.
    """
    with uow:
        # Defaults
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        # This is a bit complex for a single query across multiple tables.
        # We'll do it by iterating days or using multiple queries.
        
        days_list = []
        curr = start_date
        while curr <= end_date:
            # Query for this specific day
            d_visits = uow.session.query(func.count(Interaction.id)).filter(Interaction.type=="visit", func.date(Interaction.created_at)==curr).scalar() or 0
            d_users = uow.session.query(func.count(User.id)).filter(User.role=="USER", func.date(User.created_at)==curr).scalar() or 0
            d_owners = uow.session.query(func.count(User.id)).filter(User.role=="OWNER", func.date(User.created_at)==curr).scalar() or 0
            d_saves = uow.session.query(func.count(Favorite.id)).filter(func.date(Favorite.created_at)==curr).scalar() or 0
            d_revs = uow.session.query(func.count(Review.id)).filter(func.date(Review.created_at)==curr).scalar() or 0
            d_chats = uow.session.query(func.count(ChatMessage.id)).filter(func.date(ChatMessage.created_at)==curr).scalar() or 0
            
            days_list.append(TrendingDay(
                date=curr.strftime("%Y-%m-%d"),
                visits=d_visits,
                new_users=d_users,
                new_owners=d_owners,
                saves=d_saves,
                reviews=d_revs,
                chats=d_chats
            ))
            curr += timedelta(days=1)
            
        return days_list

def get_all_places_stats(uow: UnitOfWork) -> List[Dict]:
    """
    Get list of all places with their metadata.
    """
    with uow:
        places = uow.session.query(Place).all()
        result = []
        for p in places:
            # Aggregate stats per place
            visits = uow.session.query(func.count(Interaction.id)).filter(Interaction.place_id == p.id, Interaction.type == "visit").scalar() or 0
            saves = uow.session.query(func.count(Favorite.id)).filter(Favorite.place_id == p.id).scalar() or 0
            avg_rating = uow.session.query(func.avg(Review.rating)).filter(Review.place_id == p.id).scalar() or 0.0
            rev_count = uow.session.query(func.count(Review.id)).filter(Review.place_id == p.id).scalar() or 0
            
            result.append({
                "Place_ID": f"P-{p.id}",
                "Name": p.name,
                "Category": p.category.name if p.category else "Unknown",
                "District": "Beni Suef",
                "Visits": visits,
                "Saves": saves,
                "Rating": round(float(avg_rating), 1),
                "Reviews": rev_count,
                "Status": "Active" if p.is_active else "Suspended",
                "Added": p.created_at.strftime("%Y-%m-%d") if p.created_at else "—"
            })
        return result

def get_all_properties_stats(uow: UnitOfWork) -> List[Dict]:
    """
    Get list of all properties with their metadata.
    """
    with uow:
        properties = uow.session.query(Property).all()
        result = []
        for p in properties:
            result.append({
                "Property_ID": f"PROP-{p.id}",
                "Title": p.title,
                "Price": p.price,
                "District": "Beni Suef",
                "Status": "Available" if p.is_available else "Sold/Rented",
                "Owner": p.owner.full_name if p.owner else "Unknown",
                "Owner_Email": p.owner.email if p.owner else "—",
                "Added": p.created_at.strftime("%Y-%m-%d") if p.created_at else "—"
            })
        return result

def get_all_users_stats(uow: UnitOfWork) -> List[Dict]:
    """
    Get list of all platform users.
    """
    with uow:
        # Filter for role=USER or OWNER
        users = uow.session.query(User).filter(User.role.in_(["USER", "OWNER"])).all()
        result = []
        for u in users:
            rev_count = uow.session.query(func.count(Review.id)).filter(Review.user_id == u.id).scalar() or 0
            sav_count = uow.session.query(func.count(Favorite.id)).filter(Favorite.user_id == u.id).scalar() or 0
            
            result.append({
                "User_ID": f"U-{u.id}",
                "Name": u.full_name,
                "District": "Beni Suef",
                "Reviews": rev_count,
                "Saves": sav_count,
                "Status": "Active" if u.is_active else "Suspended",
                "Joined": u.created_at.strftime("%Y-%m-%d") if u.created_at else "—",
                "Last_Login": "—" # We don't track sessions specifically yet
            })
        return result

def get_category_stats(uow: UnitOfWork) -> List[Dict]:
    """
    Aggregation per category.
    """
    with uow:
        stats = uow.session.query(
            Category.name,
            func.count(Place.id).label("Places")
        ).outerjoin(Place).group_by(Category.name).all()
        
        return [{"Category": name, "Count": count} for name, count in stats]

def get_moderation_tasks(uow: UnitOfWork) -> Dict:
    """
    Fetch flagged reviews and pending owners.
    """
    with uow:
        # Flagged reviews (sentiment is negative or rating < 2)
        # Note: True "flagged" mechanism (user reporting) isn't fully implemented in model, 
        # so we use a heuristic for now.
        flagged = uow.session.query(Review).filter(Review.rating <= 2).limit(20).all()
        reviews_data = []
        for r in flagged:
            reviews_data.append({
                "Review_ID": f"R-{r.id}",
                "User": r.user.full_name if r.user else "Anonymous",
                "Place": r.place.name if r.place else "Unknown",
                "Review": r.comment or "—",
                "Rating": r.rating,
                "Date": r.created_at.strftime("%Y-%m-%d") if r.created_at else "—"
            })
            
        # Pending Owners (is_verified = False)
        pending = uow.session.query(User).filter(User.role == "OWNER", User.is_verified == False).limit(10).all()
        owners_data = []
        for u in pending:
            owners_data.append({
                "Owner_ID": f"OWN-{u.id}",
                "Name": u.full_name,
                "Business": "—", # Needs place linkage if exists
                "Category": "—",
                "Submitted": u.created_at.strftime("%Y-%m-%d") if u.created_at else "—"
            })
            
        return {
            "flagged_reviews": reviews_data,
            "pending_owners": owners_data
        }

def get_recent_interactions(uow: UnitOfWork, limit: int = 1000) -> List[Dict]:
    """
    Fetch recent valid visits across all places.
    Used for anomaly detection and location logic.
    """
    with uow:
        # We can reuse the InteractionRepository helper for this.
        # But for variety and speed inside service:
        interactions = uow.session.query(Interaction).filter(
            Interaction.type == "visit",
            Interaction.user_lat.isnot(None),
            Interaction.user_lon.isnot(None)
        ).order_by(Interaction.created_at.desc()).limit(limit).all()
        
        return [{
            "user_id": i.user_id,
            "place_id": i.place_id,
            "user_lat": float(i.user_lat),
            "user_lon": float(i.user_lon),
            "visited_at": i.created_at.strftime("%Y-%m-%d %H:%M:%S") if i.created_at else "",
            "cluster": i.cluster_id or 0
        } for i in interactions]

def delete_review(uow: UnitOfWork, review_id: int):
    """Delete a review."""
    with uow:
        review = uow.session.query(Review).get(review_id)
        if not review:
            return {"status": "error", "message": f"Review {review_id} not found."}
        uow.session.delete(review)
        uow.commit()
        return {"status": "success", "message": f"Review {review_id} deleted."}

def verify_owner(uow: UnitOfWork, owner_id: int, verified: bool):
    """Approve or Reject a pending owner account."""
    with uow:
        user = uow.session.query(User).get(owner_id)
        if not user or user.role != "OWNER":
            return {"status": "error", "message": f"Owner {owner_id} not found."}
        
        user.is_verified = verified
        # If rejecting, we might want to also set is_active=False or role=USER.
        # But for now, we just update is_verified.
        if not verified:
            user.is_active = False 
            
        uow.commit()
        status_text = "approved" if verified else "rejected/suspended"
        return {"status": "success", "message": f"Owner {owner_id} {status_text}."}

def update_place_status(uow: UnitOfWork, place_id_str: str, active: bool, current_admin):
    """Toggle a place's active status. Admin only."""
    require_admin(current_admin)
    try:
        # Extract numeric ID from "P-123"
        numeric_id = int(place_id_str.replace("P-", ""))
    except ValueError:
        raise APIException("Invalid Place ID format. Expected 'P-ID' (e.g., P-1001)", code=status.HTTP_400_BAD_REQUEST)
        
    with uow:
        place = uow.place_repository.get_by_id(numeric_id)
        if not place:
            raise APIException(f"Place `{place_id_str}` not found", code=status.HTTP_404_NOT_FOUND)
        
        place.is_active = active
        uow.commit()
        
        status_text = "activated" if active else "suspended"
        return {"status": "success", "message": f"Place {place_id_str} has been successfully {status_text}."}
