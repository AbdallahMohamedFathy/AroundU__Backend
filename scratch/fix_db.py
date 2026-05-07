from src.core.database import engine
from sqlalchemy import text

def fix_schema():
    with engine.connect() as conn:
        try:
            # Fix subcategories
            print("Dropping image_url from subcategories...")
            conn.execute(text("ALTER TABLE subcategories DROP COLUMN IF EXISTS image_url;"))
            
            # Fix categories
            print("Adding created_at to categories...")
            conn.execute(text("ALTER TABLE categories ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();"))
            
            conn.commit()
            print("Database schema fixed successfully.")
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()

if __name__ == "__main__":
    fix_schema()
