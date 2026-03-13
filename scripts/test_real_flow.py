import requests
import json

# Admin credentials (from your local setup or seed)
# Make sure to update these if different
ADMIN_EMAIL = "admin@aroundu.com" 
# Note: I don't know the exact admin password, assuming it's from seed_data.py
# Or I can use a script to insert directly into DB to bypass auth for this test.

def create_place_via_db():
    from src.core.database import SessionLocal
    from src.models.user import User
    from src.models.place import Place
    from src.models.interaction import Interaction
    from src.core.security import get_password_hash
    from datetime import datetime, timedelta
    import random

    db = SessionLocal()
    try:
        # 1. Create Owner
        email = "sultan_new@owner.com"
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"User {email} already exists. Deleting to recreate...")
            db.delete(existing)
            db.commit()

        owner = User(
            full_name="Sultan Elsham Owner",
            email=email,
            password_hash=get_password_hash("password123"),
            role="OWNER",
            is_active=True,
            is_verified=True
        )
        db.add(owner)
        db.flush()

        # 2. Create Place
        place = Place(
            name="Sultan Elsham - Real Data",
            description="Experience the real sultan food",
            category_id=1,
            latitude=29.0661,
            longitude=31.0994,
            owner_id=owner.id,
            is_active=True
        )
        db.add(place)
        db.flush()

        # 3. Add Sample Interactions for the last 7 days
        types = ["visit", "call", "direction", "order", "save"]
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            # Add some random number of interactions per day
            for _ in range(random.randint(5, 15)):
                inter = Interaction(
                    place_id=place.id,
                    type=random.choice(types),
                    created_at=date
                )
                db.add(inter)
        
        db.commit()
        print(f"Successfully created Place and Owner ({email}) with sample data!")
        print("Now you can login to the dashboard using:")
        print(f"Email: {email}")
        print("Password: password123")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_place_via_db()
