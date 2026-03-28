from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.interaction import Interaction
from src.repositories.base_repository import BaseRepository

class InteractionRepository(BaseRepository[Interaction]):
    def __init__(self, session: Session):
        super().__init__(Interaction, session)

    def get_by_place(self, place_id: int) -> List[Interaction]:
        """All interactions for a place (all types)."""
        return (
            self.session.query(Interaction)
            .filter(Interaction.place_id == place_id)
            .order_by(Interaction.created_at.desc())
            .all()
        )

    def get_visits_by_place(self, place_id: int) -> List[Interaction]:
        """Visit-type interactions with valid coordinates for a place."""
        return (
            self.session.query(Interaction)
            .filter(
                Interaction.place_id == place_id,
                Interaction.type == "visit",
                Interaction.user_lat.isnot(None),
                Interaction.user_lon.isnot(None),
            )
            .order_by(Interaction.created_at.desc())
            .all()
        )

    def get_recent_by_user(
        self, user_id: int, limit: int = 50
    ) -> List[Interaction]:
        """
        Return the N most recent interactions for a user across ALL places.

        Used by real-time anomaly detection to provide historical context for
        Impossible Travel and GPS Spoofing checks.
        """
        return (
            self.session.query(Interaction)
            .filter(
                Interaction.user_id == user_id,
                Interaction.user_lat.isnot(None),
                Interaction.user_lon.isnot(None),
            )
            .order_by(Interaction.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_all_valid_visits(self, limit: int = 1000) -> List[Interaction]:
        """
        Return the most recent valid visit records across ALL places.

        Used by the admin dashboard for district-wide anomaly detection
        (District Spike, Dead Zone). Includes only fully-populated rows.
        """
        return (
            self.session.query(Interaction)
            .filter(
                Interaction.type == "visit",
                Interaction.user_id.isnot(None),
                Interaction.user_lat.isnot(None),
                Interaction.user_lon.isnot(None),
                Interaction.cluster_id.isnot(None),
                Interaction.created_at.isnot(None),
            )
            .order_by(Interaction.created_at.desc())
            .limit(limit)
            .all()
        )
