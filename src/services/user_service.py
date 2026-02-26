"""
Service layer for managing users (Refactored for Phase D)
"""
from typing import List, Optional
from src.core.unit_of_work import UnitOfWork
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserUpdate
from src.core.security import get_password_hash, verify_password
from src.core.exceptions import APIException
from fastapi import status

def get_user_by_email(repo: UserRepository, email: str):
    return repo.get_by_email(email)

def get_user_by_id(repo: UserRepository, user_id: int):
    user = repo.get_by_id(user_id)
    if not user:
        raise APIException("User not found", code=status.HTTP_404_NOT_FOUND)
    return user

def get_all_users(repo: UserRepository, skip: int = 0, limit: int = 100):
    return repo.list(limit=limit, offset=skip)

def update_user_profile(uow: UnitOfWork, user_id: int, data: UserUpdate):
    with uow:
        user = uow.user_repository.get_by_id(user_id)
        if not user:
            raise APIException("User not found", code=status.HTTP_404_NOT_FOUND)

        if data.email and data.email != user.email:
            existing = uow.user_repository.get_by_email(data.email)
            if existing:
                raise APIException("Email already in use", code=status.HTTP_400_BAD_REQUEST)
            user.email = data.email

        if data.full_name is not None:
            user.full_name = data.full_name

        uow.commit()
        return uow.user_repository.get_by_id(user_id)

def change_password(uow: UnitOfWork, user_id: int, current_password: str, new_password: str):
    with uow:
        user = uow.user_repository.get_by_id(user_id)
        if not user:
            raise APIException("User not found", code=status.HTTP_404_NOT_FOUND)

        if not verify_password(current_password, user.password_hash):
            raise APIException("Current password is incorrect", code=status.HTTP_400_BAD_REQUEST)
        
        user.password_hash = get_password_hash(new_password)
        uow.commit()
        return True

def delete_user(uow: UnitOfWork, user_id: int):
    with uow:
        user = uow.user_repository.get_by_id(user_id)
        if not user:
            raise APIException("User not found", code=status.HTTP_404_NOT_FOUND)
        
        uow.user_repository.delete(user_id)
        uow.commit()
        return True
