from sqlalchemy.orm import Session
from sqlalchemy.future import select
from src.models.place import Place
from src.schemas.place import PlaceBase

def get_places(db: Session, skip: int = 0, limit: int = 100):
    result = db.execute(select(Place).offset(skip).limit(limit))
    return result.scalars().all()

def create_place(db: Session, place: PlaceBase):
    db_place = Place(**place.dict())
    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    return db_place

def get_places_by_category(db: Session, category_id: int):
    result = db.execute(select(Place).filter(Place.category_id == category_id))
    return result.scalars().all()
