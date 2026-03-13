"""
Seed script — populates the database with sample categories, places, and a
demo admin user. Safe to run multiple times (skips existing records).

Usage:
    python scripts/seed_data.py
    # or via Docker:
    docker compose exec api python scripts/seed_data.py
"""
import sys
import os

# Make sure we can import from src/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import SessionLocal
from src.core.security import get_password_hash
from src.models.user import User
from src.models.category import Category
from src.models.place import Place


def seed():
    db = SessionLocal()
    try:
        # ── Categories ────────────────────────────────────────────
        categories_data = [
            {"name": "Restaurant",  "icon": "🍽️"},
            {"name": "Cafe",        "icon": "☕"},
            {"name": "Park",        "icon": "🌳"},
            {"name": "Museum",      "icon": "🏛️"},
            {"name": "Shopping",    "icon": "🛍️"},
            {"name": "Hotel",       "icon": "🏨"},
            {"name": "Hospital",    "icon": "🏥"},
            {"name": "Gym",         "icon": "💪"},
            {"name": "Beach",       "icon": "🏖️"},
            {"name": "Pharmacy",    "icon": "💊"},
        ]

        categories = {}
        for data in categories_data:
            existing = db.query(Category).filter(Category.name == data["name"]).first()
            if not existing:
                cat = Category(**data)
                db.add(cat)
                db.flush()
                categories[data["name"]] = cat
                print(f"  [OK] Category: {data['name']}")
            else:
                categories[data["name"]] = existing
                print(f"  [SKIP] Category already exists: {data['name']}")

        db.commit()

        # ── Admin user ────────────────────────────────────────────
        admin_email = "Admin@AroundU.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                full_name="AroundU",
                email=admin_email,
                password_hash=get_password_hash("aroundu11"),
                role="ADMIN",
                is_active=True,
                is_verified=True,
            )
            db.add(admin)
            db.flush()
            print(f"\n  [OK] Admin user created: {admin_email} / admin123!")
        else:
            print(f"\n  [SKIP] Admin user already exists: {admin_email}")

        # ── Owner user ────────────────────────────────────────────
        owner_email = "owner@aroundu.com"
        owner = db.query(User).filter(User.email == owner_email).first()
        if not owner:
            owner = User(
                full_name="The Grand Kitchen Owner",
                email=owner_email,
                password_hash=get_password_hash("owner123!"),
                role="OWNER",
                is_active=True,
                is_verified=True,
            )
            db.add(owner)
            db.flush()
            print(f"  [OK] Owner user created: {owner_email} / owner123!")
        else:
            print(f"  [SKIP] Owner user already exists: {owner_email}")

        db.commit()

        # ── Demo user ─────────────────────────────────────────────
        demo_email = "demo@aroundu.com"
        demo = db.query(User).filter(User.email == demo_email).first()
        if not demo:
            demo = User(
                full_name="Demo User",
                email=demo_email,
                password_hash=get_password_hash("demo1234"),
                role="USER",
                is_active=True,
                is_verified=True,
            )
            db.add(demo)
            db.commit()
            print(f"  [OK] Demo user created:  {demo_email} / demo1234")
        else:
            print(f"  [SKIP] Demo user already exists: {demo_email}")

        # ── Places ────────────────────────────────────────────────
        places_data = [
            # Restaurants
            {
                "name": "The Grand Kitchen",
                "description": "Fine dining with international cuisine and a breathtaking rooftop view.",
                "address": "12 Main Street, Downtown",
                "phone": "+1-555-0101",
                "website": "https://grandkitchen.example.com",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "category": "Restaurant",
                "rating": 4.7,
                "owner_id": owner.id if owner else None,
            },
            {
                "name": "Street Tacos Fiesta",
                "description": "Authentic Mexican street tacos made fresh every day.",
                "address": "88 Spice Ave",
                "phone": "+1-555-0102",
                "latitude": 40.7308,
                "longitude": -73.9975,
                "category": "Restaurant",
                "rating": 4.2,
            },
            # Cafes
            {
                "name": "Brewed Awakening",
                "description": "Specialty coffee, artisan pastries, and a cosy reading corner.",
                "address": "5 Bean Lane",
                "phone": "+1-555-0201",
                "website": "https://brewedawakening.example.com",
                "latitude": 40.7219,
                "longitude": -74.0012,
                "category": "Cafe",
                "rating": 4.5,
            },
            {
                "name": "Cloud Nine Café",
                "description": "Sky-high views, great espresso, and the best cheesecake in town.",
                "address": "99 Skyline Blvd, Floor 30",
                "phone": "+1-555-0202",
                "latitude": 40.7589,
                "longitude": -73.9851,
                "category": "Cafe",
                "rating": 4.3,
            },
            # Parks
            {
                "name": "Central Meadow Park",
                "description": "A sprawling green oasis with jogging trails and weekend markets.",
                "address": "Central Park North",
                "latitude": 40.7829,
                "longitude": -73.9654,
                "category": "Park",
                "rating": 4.8,
            },
            {
                "name": "Riverside Walk",
                "description": "Scenic riverside park — perfect for cycling and family picnics.",
                "address": "1 River Road",
                "latitude": 40.7023,
                "longitude": -74.0165,
                "category": "Park",
                "rating": 4.6,
            },
            # Museums
            {
                "name": "City History Museum",
                "description": "Explore centuries of local history through immersive exhibits.",
                "address": "200 Heritage Square",
                "phone": "+1-555-0401",
                "website": "https://cityhistory.example.com",
                "latitude": 40.7411,
                "longitude": -73.9897,
                "category": "Museum",
                "rating": 4.4,
            },
            # Shopping
            {
                "name": "The Metro Mall",
                "description": "200+ stores, food court, cinema, and weekend events.",
                "address": "1 Commerce Plaza",
                "phone": "+1-555-0501",
                "latitude": 40.7505,
                "longitude": -73.9934,
                "category": "Shopping",
                "rating": 4.1,
            },
            # Hotel
            {
                "name": "Skyline Grand Hotel",
                "description": "5-star hotel with panoramic city views, spa, and rooftop pool.",
                "address": "10 Luxury Lane",
                "phone": "+1-555-0601",
                "website": "https://skylinegrand.example.com",
                "latitude": 40.7614,
                "longitude": -73.9776,
                "category": "Hotel",
                "rating": 4.9,
            },
            # Gym
            {
                "name": "Iron & Soul Gym",
                "description": "State-of-the-art equipment, personal trainers, and group classes.",
                "address": "33 Fitness Ave",
                "phone": "+1-555-0801",
                "latitude": 40.7448,
                "longitude": -74.0052,
                "category": "Gym",
                "rating": 4.3,
            },
        ]

        print("\n  Seeding places...")
        for data in places_data:
            existing = db.query(Place).filter(Place.name == data["name"]).first()
            if existing:
                print(f"  [SKIP] Place already exists: {data['name']}")
                continue

            cat_name = data.pop("category")
            cat = categories.get(cat_name)
            if not cat:
                print(f"  [WARN] Category '{cat_name}' not found, skipping {data['name']}")
                continue

            place = Place(
                **data,
                category_id=cat.id,
                is_active=True,
            )
            db.add(place)
            print(f"  [OK] Place: {place.name}")

        db.commit()
        print("\n[FINISH] Seeding complete!")
        print("─" * 42)
        print("  Admin login:  admin@aroundu.com / admin123!")
        print("  Demo login:   demo@aroundu.com  / demo1234")
        print("─" * 42)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
