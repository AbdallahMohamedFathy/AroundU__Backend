import os
import json
import logging
import firebase_admin
from firebase_admin import credentials
from typing import Optional
from src.core.config import settings

logger = logging.getLogger(__name__)

def get_firebase_app() -> firebase_admin.App:
    """
    Lazy singleton initialization for Firebase Admin SDK.
    Checks for existing apps to ensure it's initialized only once.
    
    Priority:
    1. FIREBASE_SERVICE_ACCOUNT_JSON (JSON string)
    2. FIREBASE_SERVICE_ACCOUNT_PATH (Path to JSON file)
    """
    if firebase_admin._apps:
        return firebase_admin.get_app()

    # Priority 1: Direct JSON string
    if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        try:
            service_account_info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
            cred = credentials.Certificate(service_account_info)
            logger.info("Initializing Firebase using JSON string.")
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            logger.error(f"Failed to initialize Firebase with JSON string: {e}")
            raise ValueError(f"Invalid FIREBASE_SERVICE_ACCOUNT_JSON: {e}")

    # Priority 2: File path
    service_account_path = settings.FIREBASE_SERVICE_ACCOUNT_PATH
    if not service_account_path:
        logger.error("No Firebase credentials provided in settings.")
        raise ValueError(
            "Firebase credentials missing. Provide FIREBASE_SERVICE_ACCOUNT_PATH "
            "or FIREBASE_SERVICE_ACCOUNT_JSON in settings."
        )

    if not os.path.exists(service_account_path):
        logger.error(f"Firebase service account file not found at: {service_account_path}")
        raise FileNotFoundError(f"Firebase service account file not found: {service_account_path}")

    try:
        cred = credentials.Certificate(service_account_path)
        logger.info(f"Initializing Firebase using file: {service_account_path}")
        return firebase_admin.initialize_app(cred)
    except Exception as e:
        logger.error(f"Error initializing Firebase from path {service_account_path}: {e}")
        raise
