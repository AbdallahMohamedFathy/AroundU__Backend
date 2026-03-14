from sqlalchemy import create_engine, text
from src.core.config import settings

def check_images():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, place_id, image_url, image_type, caption FROM place_images"))
        rows = result.fetchall()
        print(f"Total images found: {len(rows)}")
        for row in rows:
            print(f"ID: {row.id} | PlaceID: {row.place_id} | Type: {row.image_type} | URL: {row.image_url} | Caption: {row.caption}")

if __name__ == "__main__":
    check_images()
