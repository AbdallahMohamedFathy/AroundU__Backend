from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from src.core.config import settings

_db_url = settings.DATABASE_URL
if _db_url.startswith("postgresql://") or _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    _db_url = _db_url.replace("postgres://", "postgresql+psycopg://", 1)

engine = create_engine(
    _db_url,
    echo=settings.ENVIRONMENT == "development",
    # Connection Pool Settings
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    future=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
