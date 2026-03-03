from src.models.item import Item
from src.repositories.base_repository import BaseRepository

class ItemRepository(BaseRepository[Item]):
    def __init__(self, session):
        super().__init__(Item, session)

    def get_by_place(self, place_id: int, skip: int = 0, limit: int = 100):
        return (
            self.session.query(self.model)
            .filter(self.model.place_id == place_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_by_place(self, place_id: int):
        return (
            self.session.query(self.model)
            .filter(self.model.place_id == place_id, self.model.is_active == True)
            .all()
        )
