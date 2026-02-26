from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy.sql import select

T = TypeVar("T")

class BaseRepository(Generic[T]):
    """Base repository for common CRUD operations."""
    
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session

    def get_by_id(self, id: Any) -> Optional[T]:
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.session.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: Any) -> T:
        # Note: We don't commit here as per UoW requirements
        self.session.add(obj_in)
        self.session.flush()
        return obj_in

    def update(self, db_obj: T, obj_in: Any) -> T:
        # Note: Implementation depends on if obj_in is a dict or a schema
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
        
        self.session.add(db_obj)
        self.session.flush()
        return db_obj

    def delete(self, db_obj: T) -> T:
        self.session.delete(db_obj)
        self.session.flush()
        return db_obj
