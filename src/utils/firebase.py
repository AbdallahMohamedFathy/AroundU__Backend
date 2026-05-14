import os
import json
import logging
try:
    import firebase_admin
    from firebase_admin import credentials
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
from typing import Optional
from src.core.config import settings

logger = logging.getLogger(__name__)

def get_firebase_app():
    """
    Lazy singleton initialization for Firebase Admin SDK.
    """
    if not FIREBASE_AVAILABLE:
        logger.warning("Firebase Admin SDK is not installed. Firebase functionality is disabled.")
        return None

    if firebase_admin._apps:
        return firebase_admin.get_app()

    logger.info("=== Firebase Initialization Debug ===")
    logger.info(f"FIREBASE_SERVICE_ACCOUNT_JSON set: {bool(settings.FIREBASE_SERVICE_ACCOUNT_JSON)}")
    logger.info(f"FIREBASE_SERVICE_ACCOUNT_PATH set: {settings.FIREBASE_SERVICE_ACCOUNT_PATH}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Files in cwd: {os.listdir('.')[:20]}")
    
    # Check /app/ directory too (Docker)
    if os.path.exists('/app'):
        logger.info(f"Files in /app: {[f for f in os.listdir('/app') if 'firebase' in f.lower()]}")

    # Priority 1: Direct JSON string from env var
    if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        try:
            service_account_info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
            cred = credentials.Certificate(service_account_info)
            logger.info("✅ Firebase initialized using JSON string (env var).")
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            logger.error(f"❌ Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
            raise ValueError(f"Invalid FIREBASE_SERVICE_ACCOUNT_JSON: {e}")

    # Priority 2: File path from settings
    service_account_path = settings.FIREBASE_SERVICE_ACCOUNT_PATH
    
    # Priority 3: Auto-detect common file names
    if not service_account_path:
        search_dirs = ['.', '/app']
        candidates = ["firebase-credentials.json", "firebase-service-account.json"]
        for d in search_dirs:
            for candidate in candidates:
                full_path = os.path.join(d, candidate)
                if os.path.exists(full_path):
                    service_account_path = full_path
                    logger.info(f"✅ Auto-detected Firebase credentials at: {full_path}")
                    break
            if service_account_path:
                break

    if not service_account_path:
        logger.error("❌ No Firebase credentials found anywhere.")
        raise ValueError(
            "Firebase credentials missing. Provide FIREBASE_SERVICE_ACCOUNT_PATH "
            "or FIREBASE_SERVICE_ACCOUNT_JSON in settings."
        )

    if not os.path.exists(service_account_path):
        logger.error(f"❌ Firebase file path set but file not found: {service_account_path}")
        raise FileNotFoundError(f"Firebase service account file not found: {service_account_path}")

    try:
        cred = credentials.Certificate(service_account_path)
        logger.info(f"✅ Firebase initialized using file: {service_account_path}")
        return firebase_admin.initialize_app(cred)
    except Exception as e:
        logger.error(f"❌ Error initializing Firebase from {service_account_path}: {e}")
        raise
