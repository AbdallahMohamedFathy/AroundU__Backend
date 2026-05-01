import os
import sys
import uuid
import secrets

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import SessionLocal
from src.models.api_key import ServiceAPIKey

def create_ai_key():
    db = SessionLocal()
    try:
        # Generate a raw API Key for the user to copy
        raw_api_key = f"ai_dev_{secrets.token_hex(16)}"
        
        # We are using direct matching for now, so we store the raw key in `api_key_hash`. 
        # In production, you would hash it (e.g. using passlib).
        new_key = ServiceAPIKey(
            service_name="Test AI Chatbot",
            api_key_hash=raw_api_key, 
            permissions=["read:interactions", "read:places", "read:analytics", "read:training_data"]
        )
        
        db.add(new_key)
        db.commit()
        db.refresh(new_key)
        
        print("=========================================")
        print("✅ SUCCESS! AI API Key generated.")
        print("=========================================")
        print(f"Service Name: {new_key.service_name}")
        print(f"Your X-API-Key: {raw_api_key}")
        print("=========================================")
        print("⚠️ IMPORTANT: Copy this key now. You will need it to authorize in Swagger UI.")
        print("1. Go to Swagger UI.")
        print("2. Click the 'Authorize' Padlock (🔓) next to the AI endpoint.")
        print("3. Paste the key above into the 'Value' field and click 'Authorize'.")
        print("=========================================")
    except Exception as e:
        print(f"❌ Error creating API key: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_ai_key()
