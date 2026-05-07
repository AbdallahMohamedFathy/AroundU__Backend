from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    icon = Column(String, nullable=True) # URL or emoji/char
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    places = relationship("Place", back_populates="category")
    subcategories = relationship("SubCategory", back_populates="category", cascade="all, delete-orphan")
