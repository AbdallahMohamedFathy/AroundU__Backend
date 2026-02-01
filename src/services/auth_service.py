from sqlalchemy.orm import Session
from sqlalchemy.future import select
from fastapi import HTTPException, status
from src.models.user import User
from src.schemas.user import UserCreate, UserLogin
from src.core.security import get_password_hash, verify_password, create_access_token
from src.services.user_service import get_user_by_email

def register_user(db: Session, user_in: UserCreate):
    # Check if user exists
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=get_password_hash(user_in.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create token
    access_token = create_access_token(subject=new_user.id)
    
    return {
        "success": True,
        "token": access_token,
        "user": new_user
    }

def authenticate_user(db: Session, user_in: UserLogin):
    user = get_user_by_email(db, user_in.email)
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.id)
    
    return {
        "success": True,
        "token": access_token,
        "user": user
    }
