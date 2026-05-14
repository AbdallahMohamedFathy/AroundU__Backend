from src.core.database import SessionLocal
from src.models.user import User

db = SessionLocal()
email = "bolivar11@gmail.com"
user = db.query(User).filter(User.email == email).first()

if user:
    print(f"User found: ID={user.id}, Email={user.email}, Role={user.role}, IsActive={user.is_active}")
    # We can't check the password hash easily without passlib, but we can see if it's set
    print(f"Has password hash: {user.password_hash is not None}")
else:
    print(f"User '{email}' not found in database.")

db.close()
