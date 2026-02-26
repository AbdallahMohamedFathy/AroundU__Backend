"""
Pagination utilities
"""
from typing import List, TypeVar, Generic
from sqlalchemy.orm import Query
from math import ceil
from src.core.config import settings

T = TypeVar('T')


class PaginationParams:
    """Helper class for pagination parameters"""

    def __init__(self, page: int = 1, page_size: int = None):
        self.page = max(1, page)
        if page_size is None:
            self.page_size = settings.DEFAULT_PAGE_SIZE
        else:
            self.page_size = min(page_size, settings.MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def paginate(query: Query, page: int = 1, page_size: int = None) -> dict:
    """
    Paginate a SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Dictionary containing pagination metadata and items

    Example:
        >>> query = db.query(Place)
        >>> result = paginate(query, page=2, page_size=20)
        >>> result['items']  # List of Place objects
        >>> result['total']  # Total number of items
        >>> result['page']  # Current page number
        >>> result['total_pages']  # Total number of pages
    """
    params = PaginationParams(page, page_size)

    # Get total count
    total = query.count()

    # Calculate total pages
    total_pages = ceil(total / params.page_size) if total > 0 else 0

    # Get items for current page
    items = query.offset(params.offset).limit(params.limit).all()

    return {
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": total_pages,
        "items": items
    }
