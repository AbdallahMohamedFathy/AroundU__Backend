from src.core.database import SessionLocal
from src.models.user import User
from src.core.security import verify_password

def check_pass(email, password):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if user:
        match = verify_password(password, user.password_hash)
        print(f"User: {user.email}, Password Match: {match}")
    else:
        print(f"User {email} not found")
    db.close()

if __name__ == "__main__":
    check_pass("abdallahmohamed@gmail.com", "abdallah1234")
    check_pass("bolivar11@gmail.com", "bolivar111")
