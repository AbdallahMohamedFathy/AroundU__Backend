from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List

from src.core.database import get_db
from src.core.dependencies import verify_ai_service, limiter
from src.schemas.ai_schemas import AIInteractionResponse, AIPlaceResponse, AIAnalyticsResponse
from src.models.interaction import Interaction
from src.models.place import Place
from src.models.subcategory import SubCategory

router = APIRouter(prefix="/ai/data", tags=["AI Gateway"])

def _map_place(p: Place) -> AIPlaceResponse:
    sub_category_names = [sc.name for sc in getattr(p, "subcategories", []) if not getattr(sc, "is_deleted", False)]
    sub_category = "، ".join(sub_category_names) if sub_category_names else None

    image_url = None
    if getattr(p, "images", None):
        main_img = next((img for img in p.images if getattr(img, "image_type", None) == "main"), None)
        image_url = main_img.image_url if main_img else p.images[0].image_url

    menu_items = []
    for sc in getattr(p, "subcategories", []):
        if not getattr(sc, "is_deleted", False):
            for item in getattr(sc, "items", []):
                if getattr(item, "is_active", True) and not getattr(item, "is_deleted", False):
                    menu_items.append(item.name)
                    
    tags = []
    if getattr(p, "category", None):
        tags.append(p.category.name)
    tags.extend(sub_category_names)
    
    phone = p.phone if p.phone else None
    
    return AIPlaceResponse(
        place_id=str(p.id),
        name=p.name,
        category=p.category.name if getattr(p, "category", None) else "Unknown",
        rating=p.rating or 0.0,
        review_count=p.review_count or 0,
        lat=p.latitude,
        lng=p.longitude,
        sub_category=sub_category,
        address=p.address,
        phone=phone,
        opening_hours=getattr(p, "working_hours", None),
        description=p.description,
        price_range=None,
        image_url=image_url,
        menu_items=menu_items if menu_items else None,
        tags=tags if tags else None,
        is_open=bool(p.is_active and getattr(p, "is_accepting_orders", True))
    )

@router.get("/interactions", response_model=dict)
@limiter.limit("20/minute")
async def get_interactions(
    request: Request,
    skip: int = 0, 
    limit: int = 100,
    service = Depends(verify_ai_service("read:interactions")),
    db: Session = Depends(get_db)
):
    """Fetch sanitized user interactions."""
    limit = min(limit, 100) # Hard cap limit
    # Just a simple query for demonstration
    interactions = db.query(Interaction).order_by(Interaction.created_at.desc()).offset(skip).limit(limit).all()
    
    # We would map Interaction to AIInteractionResponse
    # Since this is a demo structure, we'll return an empty list or mock if table is empty
    return {
        "data": [
            AIInteractionResponse(
                user_id=str(i.user_id),
                event_type=i.type,
                place_id=str(i.place_id) if i.place_id else None,
                rating_value=None,
                timestamp=i.created_at
            ) for i in interactions
        ],
        "meta": {"limit": limit, "skip": skip}
    }

@router.get("/places", response_model=dict)
@limiter.limit("20/minute")
async def get_places(
    request: Request,
    category: str = None,
    skip: int = 0, 
    limit: int = 100,
    service = Depends(verify_ai_service("read:places")),
    db: Session = Depends(get_db)
):
    """Fetch sanitized places metadata."""
    limit = min(limit, 100)
    from sqlalchemy.orm import selectinload
    query = db.query(Place).options(
        selectinload(Place.category),
        selectinload(Place.images),
        selectinload(Place.subcategories).selectinload(SubCategory.items)
    )
    if category:
        # Assuming place has a category relationship or field. 
        # Using string matching or category ID based on the DB schema.
        pass
        
    places = query.offset(skip).limit(limit).all()
    
    return {
        "data": [
            _map_place(p) for p in places
        ],
        "meta": {"limit": limit, "skip": skip}
    }

@router.get("/analytics", response_model=AIAnalyticsResponse)
@limiter.limit("10/minute")
async def get_analytics(
    request: Request,
    service = Depends(verify_ai_service("read:analytics")),
    db: Session = Depends(get_db)
):
    """Pre-computed analytics for AI."""
    from sqlalchemy import func
    from sqlalchemy.orm import selectinload
    
    # 1. Top rated places
    top_rated = db.query(Place).options(
        selectinload(Place.category),
        selectinload(Place.images),
        selectinload(Place.subcategories).selectinload(SubCategory.items)
    ).filter(Place.is_active == True).order_by(Place.rating.desc()).limit(5).all()
    
    # 2. Most visited (places with most interactions)
    # Using review_count as a proxy for simplicity, or we can query interactions
    most_visited = db.query(Place).options(
        selectinload(Place.category),
        selectinload(Place.images),
        selectinload(Place.subcategories).selectinload(SubCategory.items)
    ).filter(Place.is_active == True).order_by(Place.review_count.desc()).limit(5).all()

    # 3. Trending categories
    # We find categories with the highest total review count across their places
    trending_cats = db.query(
        Place.category_id,
        func.sum(Place.review_count).label('total_reviews')
    ).filter(Place.is_active == True).group_by(Place.category_id).order_by(func.sum(Place.review_count).desc()).limit(3).all()
    
    trending_category_names = []
    if trending_cats:
        from src.models.category import Category
        cat_ids = [tc.category_id for tc in trending_cats if tc.category_id]
        if cat_ids:
            cats = db.query(Category).filter(Category.id.in_(cat_ids)).all()
            # Preserve order
            cat_map = {c.id: c.name for c in cats}
            trending_category_names = [cat_map[cid] for cid in cat_ids if cid in cat_map]

    return AIAnalyticsResponse(
        top_rated_places=[_map_place(p) for p in top_rated],
        most_visited_places=[_map_place(p) for p in most_visited],
        trending_categories=trending_category_names
    )
