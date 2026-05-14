from src.core.database import SessionLocal
from src.models.user import User

def check():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "bolivar11@gmail.com").first()
    if user:
        print(f"User: {user.email}, Role: {user.role}, Is Active: {user.is_active}, Is Verified: {user.is_verified}")
    else:
        print("User not found")
    db.close()

if __name__ == "__main__":
    check()
