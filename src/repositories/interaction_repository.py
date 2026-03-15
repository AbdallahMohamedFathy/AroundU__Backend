from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.interaction import Interaction
from src.repositories.base_repository import BaseRepository

class InteractionRepository(BaseRepository[Interaction]):
    def __init__(self, session: Session):
        super().__init__(Interaction, session)

    def get_by_place(self, place_id: int) -> List[Interaction]:
        return self.session.query(Interaction).filter(Interaction.place_id == place_id).all()

    def get_visits_by_place(self, place_id: int) -> List[Interaction]:
        return self.session.query(Interaction).filter(
            Interaction.place_id == place_id,
            Interaction.type == "visit",
            Interaction.user_lat.isnot(None),
            Interaction.user_lon.isnot(None)
        ).all()
