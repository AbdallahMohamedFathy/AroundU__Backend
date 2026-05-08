import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

engine = create_async_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+psycopg://").replace("postgres://", "postgresql+psycopg://"),
    echo=True,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

Base = declarative_base()

async def init_db():
    # Import all models here to ensure they are registered with Base
    from app.orders.models.cart import Cart
    from app.orders.models.cart_item import CartItem
    from app.orders.models.order_models import Order, OrderItem
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
