import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.core.database import AsyncSessionLocal
from app.orders.services.order_service import OrderService
from app.orders.schemas.order import OrderCreate, OrderItemCreate
from app.orders.enums.enums import OrderType

async def main():
    async with AsyncSessionLocal() as session:
        try:
            service = OrderService(session)
            
            order_data = OrderCreate(
                place_id=33,
                order_type=OrderType.CASH_ON_DELIVERY,
                full_name="Abdallah",
                phone_number="01011335761",
                address="الحي الثالث",
                notes="الاوردر يبقي سخن",
                items=[
                    OrderItemCreate(item_id=9, quantity=2)
                ]
            )
            
            # Use user_id = 1 (assuming user 1 exists)
            res = await service.checkout(1, order_data)
            print("Checkout successful:", res)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
