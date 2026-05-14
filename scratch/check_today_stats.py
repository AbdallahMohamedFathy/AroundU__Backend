import sys
import os
from datetime import date

# Add current directory to path
sys.path.append(os.getcwd())

from src.core.database import SessionLocal
from src.models.place import Place
from app.orders.models.order_models import Order
from src.models.interaction import Interaction

def check_today_stats():
    db = SessionLocal()
    today = date.today()
    print(f"Checking stats for Today: {today}")
    
    # Get any place for testing
    place = db.query(Place).first()
    if not place:
        print("No places found.")
        return
        
    print(f"Testing for Place ID: {place.id} ({place.name})")
    
    visits = db.query(Interaction).filter(
        Interaction.place_id == place.id,
        Interaction.type == 'visit',
        Interaction.created_at >= today
    ).count()
    
    orders = db.query(Order).filter(
        Order.place_id == place.id,
        Order.created_at >= today
    ).count()
    
    print(f"Today's Visits: {visits}")
    print(f"Today's Orders: {orders}")
    
    db.close()

if __name__ == "__main__":
    check_today_stats()
