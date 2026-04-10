from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc, asc
from src.models.property import Property
from src.models.property_review import PropertyReview
from src.repositories.base_repository import BaseRepository


class PropertyRepository(BaseRepository[Property]):
    def __init__(self, session: Session):
        super().__init__(Property, session)

    def get_by_id_with_images(self, property_id: int) -> Optional[Property]:
        return self.session.query(Property)\
            .options(
                selectinload(Property.images),
                selectinload(Property.reviews).selectinload(PropertyReview.user)
            )\
            .filter(Property.id == property_id).first()

    def get_my_properties(self, owner_id: int) -> List[Property]:
        return self.session.query(Property)\
            .options(
                selectinload(Property.images),
                selectinload(Property.reviews)  # No sub-load of user, review_count only
            )\
            .filter(Property.owner_id == owner_id)\
            .order_by(desc(Property.created_at)).all()

    def get_paginated_filtered(
        self,
        page: int = 1,
        page_size: int = 20,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "newest"
    ) -> Tuple[List[Property], int]:
        query = self.session.query(Property)\
            .options(
                selectinload(Property.images),
                selectinload(Property.reviews)
            )\
            .filter(Property.is_available == True)

        if min_price is not None:
            query = query.filter(Property.price >= min_price)
        if max_price is not None:
            query = query.filter(Property.price <= max_price)

        # Sorting
        if sort_by == "price_asc":
            query = query.order_by(asc(Property.price))
        elif sort_by == "price_desc":
            query = query.order_by(desc(Property.price))
        else:  # newest
            query = query.order_by(desc(Property.created_at))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return items, total
