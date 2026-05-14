from src.core.unit_of_work import UnitOfWork
from src.core.database import SessionLocal
from src.services import auth_service
from src.schemas.user import UserLogin

def test_login():
    uow = UnitOfWork(SessionLocal)
    user_in = UserLogin(email="bolivar11@gmail.com", password="bolivar111")
    try:
        res = auth_service.authenticate_user(uow, user_in)
        print("Login Success!")
        print(f"Response: {res}")
    except Exception as e:
        print(f"Login Failed: {e}")

if __name__ == "__main__":
    test_login()
