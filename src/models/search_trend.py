from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from src.core.database import Base


class SearchTrend(Base):
    __tablename__ = "search_trends"

    query = Column(String, primary_key=True, index=True)
    count = Column(Integer, default=1, nullable=False)
    last_searched_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
