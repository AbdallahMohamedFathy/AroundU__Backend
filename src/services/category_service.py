from sqlalchemy.orm import Session
from sqlalchemy.future import select
from src.models.category import Category
from src.schemas.category import CategoryBase

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    result = db.execute(select(Category).offset(skip).limit(limit))
    return result.scalars().all()

def create_category(db: Session, category: CategoryBase):
    db_category = Category(name=category.name, icon=category.icon)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category
