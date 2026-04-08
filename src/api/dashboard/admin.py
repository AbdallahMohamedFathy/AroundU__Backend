from fastapi import APIRouter, Depends
from src.core.dependencies import get_uow
from src.schemas.user import UserResponse
from src.schemas.admin import (
    UserPromotion, PlaceCreateWithOwner, PlaceCreationResponse, 
    PropertyCreateWithOwner, PropertyCreationResponse, PlatformStats, TrendingDay
)
from src.services import admin_service
from src.api.dashboard.dependencies import admin_guard
from fastapi import File, UploadFile, Query
from typing import List, Dict, Any
from datetime import date

router = APIRouter(dependencies=[Depends(admin_guard)])

@router.post("/promote/{user_id}", response_model=UserResponse)
def promote_user(
    user_id: int,
    promotion: UserPromotion,
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """
    Change a user's role. Requires ADMIN privilege.
    """
    return admin_service.promote_user(uow, user_id, promotion.role, current_user)

@router.post("/places", response_model=PlaceCreationResponse)
def create_place(
    place_in: PlaceCreateWithOwner,
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """
    Create a new place and automatically create its owner account.
    """
    return admin_service.create_place_with_owner(uow, place_in, current_user)

@router.post("/properties", response_model=PropertyCreationResponse)
def create_property(
    property_in: PropertyCreateWithOwner,
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """
    Create a new property and automatically create its owner account.
    """
    return admin_service.create_property_with_owner(uow, property_in, current_user)

@router.post("/properties/{property_id}/images")
def upload_property_images(
    property_id: int,
    images: List[UploadFile] = File(...),
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """
    Upload images for an existing property (max 5 total). Requires ADMIN privilege.
    """
    return admin_service.upload_property_images(uow, property_id, images, current_user)

# --- Platform Statistics Endpoints ---

@router.get("/stats/overview", response_model=PlatformStats)
def get_platform_overview(
    start_date: date = Query(None),
    end_date: date = Query(None),
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Get high-level KPI metrics for the entire platform."""
    return admin_service.get_platform_stats(uow, start_date, end_date)

@router.get("/stats/trending", response_model=List[TrendingDay])
def get_platform_trending(
    start_date: date = Query(None),
    end_date: date = Query(None),
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Get daily trends (Visits, Signups, etc.) across the platform."""
    return admin_service.get_platform_trending(uow, start_date, end_date)

@router.get("/stats/places")
def get_all_places_stats(
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Get a list of all places with their metadata and performance stats."""
    return admin_service.get_all_places_stats(uow)

@router.get("/stats/users")
def get_all_users_stats(
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Get a list of all users and their basic statistics."""
    return admin_service.get_all_users_stats(uow)

@router.get("/stats/categories")
def get_category_analytics(
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Get distribution and performance data per category."""
    return admin_service.get_category_stats(uow)

@router.get("/stats/properties")
def get_all_properties_stats(
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Get a list of all properties with their metadata and performance stats."""
    return admin_service.get_all_properties_stats(uow)

@router.get("/moderation/pending")
def get_moderation_pending(
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Get pending owner requests and flagged reviews."""
    return admin_service.get_moderation_tasks(uow)

@router.get("/interactions/recent")
def get_recent_interactions(
    limit: int = 1000,
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Get recent valid visits for anomaly detection analysis."""
    return admin_service.get_recent_interactions(uow, limit)

# --- Moderation Actions ---

@router.delete("/reviews/{review_id}")
def delete_review(
    review_id: int,
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Delete a flagged review. Requires ADMIN privilege."""
    return admin_service.delete_review(uow, review_id)

@router.post("/owners/{owner_id}/verify")
def verify_owner(
    owner_id: int,
    verified: bool = Query(..., description="True to approve, False to reject"),
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Approve or Reject a pending owner account. Requires ADMIN privilege."""
    return admin_service.verify_owner(uow, owner_id, verified)

# --- Database Management (Generic CRUD) ---

@router.get("/db/tables")
def list_db_tables(
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """List all database tables. Requires ADMIN privilege."""
    return admin_service.get_db_tables(uow, current_user)

@router.get("/db/table/{table_name}")
def get_table_content(
    table_name: str,
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Fetch all records from a specific table. Requires ADMIN privilege."""
    return admin_service.get_table_data(uow, table_name, current_user)

@router.post("/db/table/{table_name}")
def insert_table_record(
    table_name: str,
    data: Dict[str, Any],
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Insert a new record into a table. Requires ADMIN privilege."""
    return admin_service.execute_db_operation(uow, table_name, "INSERT", data, 0, current_user)

@router.put("/db/table/{table_name}/{row_id}")
def update_table_record(
    table_name: str,
    row_id: int,
    data: Dict[str, Any],
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Update an existing record in a table. Requires ADMIN privilege."""
    return admin_service.execute_db_operation(uow, table_name, "UPDATE", data, row_id, current_user)

@router.delete("/db/table/{table_name}/{row_id}")
def delete_table_record(
    table_name: str,
    row_id: int,
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """Delete a record from a table. Requires ADMIN privilege."""
    return admin_service.execute_db_operation(uow, table_name, "DELETE", {}, row_id, current_user)
