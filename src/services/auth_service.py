"""
Service layer for authentication (Refactored for Phase D)
"""
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import status, BackgroundTasks

from src.core.unit_of_work import UnitOfWork
from src.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from src.core.exceptions import APIException
from src.core.config import settings
from src.schemas.user import UserCreate, UserLogin, UserResponse
from src.models.token import RefreshToken


def register_user(uow: UnitOfWork, user_in: UserCreate):
    with uow:
        # Normalize email
        email = user_in.email.lower().strip()
        existing_user = uow.user_repository.get_by_email(email)
        if existing_user:
            raise APIException("Email already registered", code=status.HTTP_400_BAD_REQUEST)
        
        from src.models.user import User
        new_user = User(
            email=email,
            full_name=user_in.full_name,
            password_hash=get_password_hash(user_in.password),
            verification_token=secrets.token_urlsafe(32),
        )

        uow.user_repository.add(new_user)
        uow.session.flush()

        access_token = create_access_token(
            subject=new_user.id,
            extra_data={"role": new_user.role, "email": new_user.email}
        )
        refresh_token = create_refresh_token(subject=new_user.id)
        
        # Store refresh token in the dedicated table
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        db_refresh_token = RefreshToken(
            user_id=new_user.id,
            token_hash=get_password_hash(refresh_token),
            family_id=str(uuid.uuid4()),
            expires_at=expires_at
        )
        uow.session.add(db_refresh_token)
        
        uow.commit()

        user_response = UserResponse.model_validate(new_user)

        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer", 
            "user": user_response
        }

def authenticate_user(uow: UnitOfWork, user_in: UserLogin):
    with uow:
        email = user_in.email.lower().strip()
        user = uow.user_repository.get_by_email(email)
        if not user or not verify_password(user_in.password, user.password_hash):
            raise APIException("Incorrect email or password", code=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            raise APIException("Account is deactivated", code=status.HTTP_403_FORBIDDEN)
        
        access_token = create_access_token(
            subject=user.id,
            extra_data={"role": user.role, "email": user.email}
        )
        refresh_token = create_refresh_token(subject=user.id)
        
        # Store refresh token in the dedicated table (supports multiple sessions)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=get_password_hash(refresh_token),
            family_id=str(uuid.uuid4()),
            expires_at=expires_at
        )
        uow.session.add(db_refresh_token)
        
        uow.commit()
        
        user_response = UserResponse.model_validate(user)

        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer", 
            "user": user_response
        }

def refresh_access_token(uow: UnitOfWork, user_id: str, refresh_token: str):
    with uow:
        # 1. Get all active refresh tokens for this user
        db_tokens = uow.session.query(RefreshToken).filter(
            RefreshToken.user_id == int(user_id),
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        ).all()
        
        # 2. Find the matching token
        target_token = None
        for t in db_tokens:
            if verify_password(refresh_token, t.token_hash):
                target_token = t
                break
        
        if not target_token:
            raise APIException("Invalid or expired refresh token", code=status.HTTP_401_UNAUTHORIZED)
            
        # 3. Check if user is still active
        user = uow.user_repository.get_by_id(int(user_id))
        if not user or not user.is_active:
            raise APIException("Account is deactivated", code=status.HTTP_403_FORBIDDEN)
            
        # 4. Generate new tokens (Rotation)
        new_access_token = create_access_token(
            subject=user.id,
            extra_data={"role": user.role, "email": user.email}
        )
        new_refresh_token_str = create_refresh_token(subject=user.id)
        
        # 5. Update the DB: Revoke/Delete old, Add new (same family)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        rotated_token = RefreshToken(
            user_id=user.id,
            token_hash=get_password_hash(new_refresh_token_str),
            family_id=target_token.family_id,
            expires_at=expires_at
        )
        
        uow.session.delete(target_token) # Or target_token.is_revoked = True
        uow.session.add(rotated_token)
        uow.commit()
        
        return {
            "access_token": new_access_token, 
            "refresh_token": new_refresh_token_str,
            "token_type": "bearer"
        }

def verify_email(uow: UnitOfWork, token: str):
    with uow:
        user = uow.user_repository.get_by_verification_token(token)
        if not user:
            raise APIException("Invalid verification token", code=status.HTTP_400_BAD_REQUEST)
        
        user.is_verified = True
        user.verification_token = None
        uow.commit()
        return True

import hashlib
from src.utils.email import send_password_reset_email

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def request_password_reset(uow: UnitOfWork, email: str, background_tasks: BackgroundTasks) -> str:
    from src.core.logger import logger
    from src.models.password_reset_token import PasswordResetToken
    with uow:
        user = uow.user_repository.get_by_email(email)
        if not user or not user.is_active:
            return ""   # Avoid email enumeration

        # Invalidate old tokens
        uow.session.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False
        ).update({"is_used": True})
        
        # Generate raw token and hash it
        raw_token = secrets.token_urlsafe(32)
        token_hash = _hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        reset_entry = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        uow.session.add(reset_entry)
        uow.commit()

        background_tasks.add_task(
            send_password_reset_email,
            email=user.email,
            token=raw_token,
            user_name=user.full_name
        )
        logger.info(f"[RESET] Password reset email queued for {user.email}")
        return raw_token

def verify_reset_token(uow: UnitOfWork, raw_token: str) -> bool:
    from src.models.password_reset_token import PasswordResetToken
    with uow:
        token_hash = _hash_token(raw_token)
        reset_entry = uow.session.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash
        ).first()

        if not reset_entry or reset_entry.is_used or reset_entry.expires_at < datetime.now(timezone.utc):
            raise APIException("Invalid or expired reset token", code=status.HTTP_400_BAD_REQUEST)

        return True

def reset_password(uow: UnitOfWork, raw_token: str, new_password: str):
    from src.models.password_reset_token import PasswordResetToken
    with uow:
        token_hash = _hash_token(raw_token)
        reset_entry = uow.session.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash
        ).first()
        
        if not reset_entry or reset_entry.is_used or reset_entry.expires_at < datetime.now(timezone.utc):
            raise APIException("Invalid, used, or expired reset token", code=status.HTTP_400_BAD_REQUEST)
            
        user = uow.user_repository.get_by_id(reset_entry.user_id)
        if not user:
            raise APIException("User not found", code=status.HTTP_404_NOT_FOUND)
        if not user.is_active:
            raise APIException("Account is deactivated", code=status.HTTP_403_FORBIDDEN)

        # Update user password
        user.password_hash = get_password_hash(new_password)

        # Mark token as used
        reset_entry.is_used = True

        # Revoke all existing refresh tokens to kick out any active sessions
        uow.session.query(RefreshToken).filter(
            RefreshToken.user_id == user.id
        ).delete()

        uow.commit()
        return True

def social_login(uow: UnitOfWork, data: Any):
    from firebase_admin import auth
    from src.utils.firebase import get_firebase_app
    
    # Ensure Firebase is initialized
    try:
        get_firebase_app()
    except Exception as e:
        raise APIException(f"Firebase not configured: {e}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        # Verify the Firebase token
        decoded_token = auth.verify_id_token(data.id_token)
        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        name = decoded_token.get('name', 'User')
        # Detect provider from Firebase token
        provider = decoded_token.get('firebase', {}).get('sign_in_provider', 'google.com')
        
        if not firebase_uid:
            raise APIException("Invalid ID token", code=status.HTTP_400_BAD_REQUEST)
    except APIException:
        raise
    except Exception as e:
        raise APIException(f"Firebase authentication failed: {str(e)}", code=status.HTTP_401_UNAUTHORIZED)
        
    with uow:
        # 1. Check if user exists by firebase_uid
        user = uow.user_repository.get_by_firebase_uid(firebase_uid)
        
        # 2. If not found by firebase_uid, check by email (Account linking)
        if not user and email:
            user = uow.user_repository.get_by_email(email)
            if user:
                user.firebase_uid = firebase_uid
                user.provider = provider
        
        # 3. If still not found, create new user
        if not user:
            from src.models.user import User
            user = User(
                email=email,
                full_name=name,
                firebase_uid=firebase_uid,
                provider=provider,
                is_verified=True,
            )
            uow.user_repository.add(user)
            uow.session.flush()
            
        if not user.is_active:
            raise APIException("Account is deactivated", code=status.HTTP_403_FORBIDDEN)
                
        # 4. Generate Backend JWT Tokens
        access_token = create_access_token(
            subject=user.id,
            extra_data={"role": user.role, "email": user.email}
        )
        refresh_token = create_refresh_token(subject=user.id)
        
        # Store refresh token in the dedicated table
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=get_password_hash(refresh_token),
            family_id=str(uuid.uuid4()),
            expires_at=expires_at
        )
        uow.session.add(db_refresh_token)
        
        uow.commit()
        
        user_response = UserResponse.model_validate(user)

        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer", 
            "user": user_response
        }

