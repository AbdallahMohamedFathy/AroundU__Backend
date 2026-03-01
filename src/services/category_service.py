"""
Service layer for managing categories (Refactored for Phase D)
"""
from typing import List, Optional
from src.core.unit_of_work import UnitOfWork
from src.repositories.category_repository import CategoryRepository
from src.schemas.category import CategoryBase
from src.core.exceptions import APIException
from fastapi import status
from src.schemas.category import CategoryResponse

def get_categories(repo: CategoryRepository, skip: int = 0, limit: int = 100):
    return repo.get_all(skip=skip, limit=limit)

def get_category_by_id(repo: CategoryRepository, category_id: int):
    cat = repo.get_by_id(category_id)
    if not cat:
        raise APIException("Category not found", code=status.HTTP_404_NOT_FOUND)
    return cat

def create_category(uow: UnitOfWork, category: CategoryBase):
    with uow:
        existing = uow.category_repository.get_by_name(category.name)
        if existing:
            raise APIException("Category with this name already exists", code=status.HTTP_400_BAD_REQUEST)
        
        from src.models.category import Category # Lazy import
        db_category = Category(name=category.name, icon=category.icon)
        uow.category_repository.create(db_category)
        uow.commit()
        return CategoryResponse.model_validate(db_category)

def update_category(uow: UnitOfWork, category_id: int, category_data: CategoryBase):
    with uow:
        cat = uow.category_repository.get_by_id(category_id)
        if not cat:
            raise APIException("Category not found", code=status.HTTP_404_NOT_FOUND)
            
        if category_data.name and category_data.name != cat.name:
            conflict = uow.category_repository.get_by_name(category_data.name)
            if conflict:
                raise APIException("Category with this name already exists", code=status.HTTP_400_BAD_REQUEST)
        
        if category_data.name is not None:
            cat.name = category_data.name
        if category_data.icon is not None:
            cat.icon = category_data.icon
            
        uow.commit()
        return cat

def delete_category(uow: UnitOfWork, category_id: int):
    with uow:
        cat = uow.category_repository.get_by_id(category_id)
        if not cat:
            raise APIException("Category not found", code=status.HTTP_404_NOT_FOUND)
        uow.category_repository.delete(cat)
        uow.commit()
        return True
