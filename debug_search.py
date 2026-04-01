import sys
import os
import traceback

sys.path.append(os.getcwd())

from src.core.database import SessionLocal
from src.core.unit_of_work import UnitOfWork
from src.services.search_service import search_places

def main():
    uow = UnitOfWork(SessionLocal)
    try:
        res = search_places(uow, query="مطعم", limit=20)
        print("Success:", res)
    except Exception as e:
        print("Error:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
