"""
Service layer for searching places (Refactored for Phase D)
"""
from typing import List, Optional, Dict
from src.core.unit_of_work import UnitOfWork
from src.repositories.place_repository import PlaceRepository
from src.repositories.search_repository import SearchRepository

def search_places(uow: UnitOfWork, query: str = None, category: str = None, user_id: int = None):
    with uow:
        places = uow.place_repository.search(query=query, category=category)
        
        if query and user_id:
            from src.models.search_history import SearchHistory # Lazy import
            uow.search_repository.add(SearchHistory(user_id=user_id, query=query))
            uow.commit()
            
        return places

def get_recent_searches(repo: SearchRepository, user_id: int, limit: int = 5):
    return repo.get_recent(user_id, limit)

def get_trending_searches(repo: SearchRepository, limit: int = 5):
    return repo.get_trending(limit)
