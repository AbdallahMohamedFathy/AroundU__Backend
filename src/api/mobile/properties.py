from typing import List, Optional
from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from src.core.dependencies import get_current_user, get_uow
from src.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse, PropertyMyResponse, PropertyListResponse
from src.services import property_service
from src.repositories.property_repository import PropertyRepository

router = APIRouter()

# ─── GET all (must come before /{id}) ───────────────────────────────────────
@router.get("/", response_model=PropertyListResponse)
def list_properties(
    page: int = 1,
    limit: int = 20,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort: str = "newest",
    uow=Depends(get_uow)
):
    repo = PropertyRepository(uow.session)
    return property_service.get_properties(
        repo, 
        page=page, 
        limit=limit, 
        min_price=min_price, 
        max_price=max_price, 
        sort_by=sort
    )

# ─── GET my properties ───────────────────────────────────────────────────────
@router.get("/my", response_model=List[PropertyMyResponse])
def get_my_properties(
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    repo = PropertyRepository(uow.session)
    return property_service.get_my_properties(repo, current_user)

# ─── GET single ─────────────────────────────────────────────────────────────
@router.get("/{id}", response_model=PropertyResponse)
def get_property(
    id: int,
    uow=Depends(get_uow)
):
    repo = PropertyRepository(uow.session)
    return property_service.get_property_by_id(repo, id)

# ─── POST create ─────────────────────────────────────────────────────────────
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PropertyResponse)
def create_property(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    images: List[UploadFile] = File([]),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    property_data = PropertyCreate(
        title=title,
        description=description,
        price=price,
        latitude=lat,
        longitude=lng
    )
    repo = PropertyRepository(uow.session)
    return property_service.create_property(repo, property_data, images, current_user)

# ─── PUT update ──────────────────────────────────────────────────────────────
@router.put("/{id}", response_model=PropertyResponse)
def update_property(
    id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    lat: Optional[float] = Form(None),
    lng: Optional[float] = Form(None),
    is_available: Optional[bool] = Form(None),
    main_image_url: Optional[str] = Form(None),
    image_ids_to_delete: Optional[List[int]] = Form(None),
    images: List[UploadFile] = File([]),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    update_data = {}
    if title is not None: update_data["title"] = title
    if description is not None: update_data["description"] = description
    if price is not None: update_data["price"] = price
    if lat is not None: update_data["latitude"] = lat
    if lng is not None: update_data["longitude"] = lng
    if is_available is not None: update_data["is_available"] = is_available
    if main_image_url is not None: update_data["main_image_url"] = main_image_url
    update_data["image_ids_to_delete"] = image_ids_to_delete or []

    property_data = PropertyUpdate(**update_data)
    repo = PropertyRepository(uow.session)
    return property_service.update_property(repo, id, property_data, images, current_user)

# ─── DELETE ──────────────────────────────────────────────────────────────────
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(
    id: int,
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    repo = PropertyRepository(uow.session)
    property_service.delete_property(repo, id, current_user)
    return None
