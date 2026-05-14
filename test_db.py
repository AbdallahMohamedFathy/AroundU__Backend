import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from src.models.item import Item

async def main():
    async with AsyncSessionLocal() as session:
        try:
            item_id = 9
            res = await session.execute(select(Item).where(Item.id == item_id))
            db_item = res.scalars().first()
            if db_item:
                print("Item name:", db_item.name)
                print("Item price:", float(db_item.price))
            else:
                print("Item not found")
        except Exception as e:
            print("Error:", repr(e))

if __name__ == "__main__":
    asyncio.run(main())
