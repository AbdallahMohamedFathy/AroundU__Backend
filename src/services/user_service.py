from sqlalchemy.orm import Session
from sqlalchemy.future import select
from src.models.user import User

def get_user_by_email(db: Session, email: str):
    result = db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

def get_user_by_id(db: Session, user_id: int):
    result = db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()