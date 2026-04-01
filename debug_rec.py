import sys
import os
import asyncio

sys.path.append(os.getcwd())

from src.core.database import SessionLocal
from src.core.unit_of_work import UnitOfWork
from src.services.recommendation_service import get_recommendations

def main():
    db = SessionLocal()
    try:
        # Pass coordinates somewhere in Egypt (AroundU defaults typically)
        res = get_recommendations(db, latitude=30.0444, longitude=31.2357, limit=1)
        import pprint
        pprint.pprint(res)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
