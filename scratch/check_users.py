from src.core.database import SessionLocal
from src.models.user import User

def check(email):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"User: {user.email}, Role: {user.role}, Is Active: {user.is_active}, Is Verified: {user.is_verified}, Type: {user.owner_type}")
    else:
        print(f"User {email} not found")
    db.close()

if __name__ == "__main__":
    check("abdallahmohamed@gmail.com")
    check("bolivar11@gmail.com")
