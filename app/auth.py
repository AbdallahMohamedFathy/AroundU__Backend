import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.core.config import settings
# Use the project's real security settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/mobile/auth/login")

# Mock User model – replace with real ORM model
class User:
    def __init__(self, id: int, username: str, role: str):
        self.id = id
        self.username = username
        self.role = role

# In‑memory user store for demo purposes
_FAKE_USERS_DB = {
    "alice": User(id=1, username="alice", role="user"),
    "bob": User(id=2, username="bob", role="owner"),
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # For now, we return a User object with the REAL ID. 
    # To test as owner, you can check if the ID is in a list or just set it based on your test user.
    # In full integration, fetch user from DB here.
    user_role = "owner" if int(user_id) == 1 else "user" # Example: ID 1 is owner
    return User(id=int(user_id), username=f"user_{user_id}", role=user_role)

def get_current_active_user(current_user: User = Depends(get_current_user)):
    # Here you could check if the user is active, banned, etc.
    return current_user
