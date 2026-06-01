from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from src.models.item import Item
from src.repositories.base_repository import BaseRepository

class ItemRepository(BaseRepository[Item]):
    def __init__(self, session: Session):
        super().__init__(Item, session)

    def get_by_id(self, id: int) -> Optional[Item]:
        return self.session.query(self.model).options(joinedload(self.model.subcategory)).filter(self.model.id == id).first()

    def get_by_subcategory(self, sub_category_id: int) -> List[Item]:
        return self.session.query(self.model).options(joinedload(self.model.subcategory)).filter(
            self.model.sub_category_id == sub_category_id,
            self.model.is_deleted == False
        ).all()

    def get_by_name_and_subcategory(self, name: str, sub_category_id: int) -> Optional[Item]:
        return self.session.query(self.model).filter(
            self.model.name == name,
            self.model.sub_category_id == sub_category_id,
            self.model.is_deleted == False
        ).first()

    def search_items(
        self, 
        name: Optional[str] = None, 
        skip: int = 0, 
        limit: int = 10,
        sub_category_id: Optional[int] = None,
        place_id: Optional[int] = None
    ) -> Tuple[List[Item], int]:
        from src.models.subcategory import SubCategory
        query = self.session.query(self.model).options(joinedload(self.model.subcategory)).filter(self.model.is_deleted == False)
        
        if place_id:
            query = query.join(SubCategory).filter(SubCategory.place_id == place_id)
        
        if name:
            query = query.filter(self.model.name.ilike(f"%{name}%"))
        
        if sub_category_id:
            query = query.filter(self.model.sub_category_id == sub_category_id)
            
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return items, total

    def get_by_place(self, place_id: int) -> List[Item]:
        from src.models.subcategory import SubCategory
        return self.session.query(self.model).options(joinedload(self.model.subcategory)).join(
            SubCategory,
            self.model.sub_category_id == SubCategory.id
        ).filter(
            SubCategory.place_id == place_id,
            SubCategory.is_deleted == False,
            self.model.is_deleted == False
        ).all()

    def get_top_by_place(self, place_id: int, limit: int = 4) -> List[Item]:
        from src.models.subcategory import SubCategory
        from app.orders.models.order_models import OrderItem, Order
        from sqlalchemy import func

        order_counts = (
            self.session.query(
                OrderItem.item_id,
                func.sum(OrderItem.quantity).label("total_ordered"),
            )
            .join(Order, OrderItem.order_id == Order.id)
            .filter(Order.place_id == place_id)
            .group_by(OrderItem.item_id)
            .subquery()
        )

        return (
            self.session.query(self.model)
            .options(joinedload(self.model.subcategory))
            .join(SubCategory, self.model.sub_category_id == SubCategory.id)
            .outerjoin(order_counts, self.model.id == order_counts.c.item_id)
            .filter(
                SubCategory.place_id == place_id,
                SubCategory.is_deleted == False,
                self.model.is_deleted == False,
                self.model.is_available == True,
            )
            .order_by(func.coalesce(order_counts.c.total_ordered, 0).desc())
            .limit(limit)
            .all()
        )
