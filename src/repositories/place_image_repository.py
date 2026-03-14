from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.place_image import PlaceImage
from src.repositories.base_repository import BaseRepository

class PlaceImageRepository(BaseRepository[PlaceImage]):
    """Repository for PlaceImage model."""
    
    def __init__(self, session: Session):
        super().__init__(PlaceImage, session)

    def get_by_place(self, place_id: int) -> List[PlaceImage]:
        return self.session.query(PlaceImage)\
            .filter(PlaceImage.place_id == place_id).all()
