from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base


class AIInteraction(Base):
    """Persists every chatbot round-trip for auditing and analytics."""

    __tablename__ = "ai_interactions"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id    = Column(String(64), nullable=False, index=True)

    # Request
    message       = Column(Text, nullable=False)
    user_lat      = Column(Float, nullable=True)
    user_lon      = Column(Float, nullable=True)

    # Response
    reply         = Column(Text, nullable=True)
    intent        = Column(String(128), nullable=True)
    confidence    = Column(Float, nullable=True)
    entities      = Column(JSON, nullable=True)
    best_place    = Column(JSON, nullable=True)   # raw place object returned by AI

    # Meta
    latency_ms    = Column(Integer, nullable=True)  # round-trip time in ms
    is_fallback   = Column(Integer, default=0)       # 1 if AI was unreachable
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", backref="ai_interactions")
