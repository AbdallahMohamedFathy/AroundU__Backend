"""
Service layer for authentication (Refactored for Phase D)
"""
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from src.core.unit_of_work import UnitOfWork
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate, UserLogin, UserResponse
from src.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from src.core.exceptions import APIException
from fastapi import status
from datetime import datetime, timezone, timedelta


def register_user(uow: UnitOfWork, user_in: UserCreate):
    with uow:
        existing_user = uow.user_repository.get_by_email(user_in.email)
        if existing_user:
            raise APIException("Email already registered", code=status.HTTP_400_BAD_REQUEST)
        
        from src.models.user import User
        new_user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            password_hash=get_password_hash(user_in.password),
            verification_token=secrets.token_urlsafe(32),
        )

        uow.user_repository.add(new_user)
        uow.session.flush()

        access_token = create_access_token(subject=new_user.id)
        refresh_token = create_refresh_token(subject=new_user.id)

        new_user.hashed_refresh_token = get_password_hash(refresh_token)
        uow.commit()

        user_response = UserResponse.model_validate(new_user)

        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer", 
            "user": user_response
        }

def authenticate_user(uow: UnitOfWork, user_in: UserLogin):
    with uow:
        user = uow.user_repository.get_by_email(user_in.email)
        if not user or not verify_password(user_in.password, user.password_hash):
            raise APIException("Incorrect email or password", code=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            raise APIException("Account is deactivated", code=status.HTTP_403_FORBIDDEN)
        
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        user.hashed_refresh_token = get_password_hash(refresh_token)
        uow.commit()
        
        user_response = UserResponse.model_validate(user)

        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer", 
            "user": user_response
        }

def refresh_access_token(uow: UnitOfWork, user_id: str, refresh_token: str):
    with uow:
        user = uow.user_repository.get_by_id(int(user_id))
        if not user or not user.hashed_refresh_token:
            raise APIException("Invalid refresh token", code=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            raise APIException("Account is deactivated", code=status.HTTP_403_FORBIDDEN)
            
        if not verify_password(refresh_token, user.hashed_refresh_token):
            raise APIException("Invalid or expired refresh token", code=status.HTTP_401_UNAUTHORIZED)
            
        new_access_token = create_access_token(subject=user.id)
        return {"access_token": new_access_token, "token_type": "bearer"}

def verify_email(uow: UnitOfWork, token: str):
    with uow:
        user = uow.user_repository.get_by_verification_token(token)
        if not user:
            raise APIException("Invalid verification token", code=status.HTTP_400_BAD_REQUEST)
        
        user.is_verified = True
        user.verification_token = None
        uow.commit()
        return True

def request_password_reset(uow: UnitOfWork, email: str) -> str:
    with uow:
        user = uow.user_repository.get_by_email(email)
        if not user:
            return ""   # Avoid email enumeration
        
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(minutes=30)
        uow.commit()
        return token

def reset_password(uow: UnitOfWork, token: str, new_password: str):
    with uow:
        user = uow.user_repository.get_by_reset_token(token)
        if user.reset_token_expires < datetime.now(timezone.utc):
            raise APIException("Invalid or expired reset token")
        
        user.password_hash = get_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        uow.commit()
        return True
