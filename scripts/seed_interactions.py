import sys
import os
import random
from datetime import datetime, timedelta

# Added current directory to path to reach src
sys.path.append(os.getcwd())

try:
    from src.core.database import SessionLocal
    from src.models.interaction import Interaction
    from src.models.user import User

    db = SessionLocal()
    try:
        place_id = 9  # Sultan Elsham
        owner_id = 11  # AroundU(user)
        user_id = 11   # Use valid user ID (the owner themselves for testing)
        
        # Types of interactions to seed
        types = ['visit', 'save', 'direction', 'call', 'order']
        
        print(f"Seeding interactions for Place ID {place_id}...")
        
        # Seed data for the last 60 days to allow for delta calculation
        for i in range(60):
            date = datetime.now() - timedelta(days=i)
            
            # More interactions on recent days, fewer on older days to simulate growth
            count = random.randint(5, 15) if i < 30 else random.randint(2, 8)
            
            for _ in range(count):
                itype = random.choice(types)
                
                interaction = Interaction(
                    place_id=place_id,
                    user_id=user_id,
                    type=itype,
                    created_at=date,
                    user_lat=29.0661 + (random.random() - 0.5) * 0.01,
                    user_lon=31.0994 + (random.random() - 0.5) * 0.01
                )
                db.add(interaction)
        
        db.commit()
        print("Successfully seeded interactions data!")
        
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()
except ImportError as e:
    print(f"Import error: {e}. Make sure to run this script from the project root.")
