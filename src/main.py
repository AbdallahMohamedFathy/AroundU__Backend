import os

from fastapi import FastAPI, Depends, Request, HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from slowapi.errors import RateLimitExceeded

# Routers
from src.api.mobile import auth as mobile_auth
from src.api.mobile import places as mobile_places
from src.api.mobile import reviews as mobile_reviews
from src.api.mobile import categories as mobile_categories
from src.api.mobile import search as mobile_search
from src.api.mobile import favorites as mobile_favorites
from src.api.mobile import items as mobile_items
from src.api.mobile import interactions as mobile_interactions
from src.api.mobile import recommendations as mobile_recommendations
from src.api.mobile import properties as mobile_properties
from src.api.mobile import notifications as mobile_notifications
from src.api.mobile import ai as mobile_ai

from src.api.dashboard import places as dashboard_places
from src.api.dashboard import items as dashboard_items
from src.api.dashboard import upload as dashboard_upload
from src.api.dashboard import categories as dashboard_categories
from src.api.dashboard import admin as dashboard_admin
from src.api.dashboard import owner as dashboard_owner

# Menu Management
from src.api.routes import categories as menu_categories
from src.api.routes import subcategories as menu_subcategories
from src.api.routes import items as menu_items

# Core
from src.core.config import settings
from src.core.database import get_db
from src.core.logger import logger
from src.core.dependencies import limiter

from src.core.exceptions import (
    APIException,
    api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
    rate_limit_handler,
    permission_exception_handler
)

# ─────────────────────────────────────────────

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AroundU – location-based place discovery API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

@app.on_event("startup")
def on_startup():
    from sqlalchemy import text
    from src.core.database import engine
    logger.info("Running startup migrations...")
    with engine.connect() as conn:
        try:
            # Check for owner_type in users
            check = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='users' AND column_name='owner_type';"
            )).fetchone()
            if not check:
                logger.warning("Column 'owner_type' missing in 'users' table. Adding it...")
                conn.execute(text("ALTER TABLE users ADD COLUMN owner_type VARCHAR;"))
                conn.commit()
                logger.info("Column 'owner_type' added successfully.")
            
            # Check for request_id in notifications
            check_notif = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='notifications' AND column_name='request_id';"
            )).fetchone()
            if not check_notif:
                logger.warning("Column 'request_id' missing in 'notifications' table. Adding it...")
                conn.execute(text("ALTER TABLE notifications ADD COLUMN request_id INTEGER REFERENCES notification_requests(id) ON DELETE SET NULL;"))
                conn.commit()
                logger.info("Column 'request_id' added successfully.")

            # ── ai_interactions table ──────────────────────────────────────
            ai_table = conn.execute(text(
                "SELECT to_regclass('public.ai_interactions');"
            )).scalar()
            if not ai_table:
                logger.warning("Table 'ai_interactions' missing. Creating it...")
                conn.execute(text("""
                    CREATE TABLE ai_interactions (
                        id          SERIAL PRIMARY KEY,
                        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        session_id  VARCHAR(64) NOT NULL,
                        message     TEXT NOT NULL,
                        user_lat    FLOAT,
                        user_lon    FLOAT,
                        reply       TEXT,
                        intent      VARCHAR(128),
                        confidence  FLOAT,
                        entities    JSONB,
                        best_place  JSONB,
                        latency_ms  INTEGER,
                        is_fallback INTEGER DEFAULT 0,
                        created_at  TIMESTAMPTZ DEFAULT NOW()
                    );
                    CREATE INDEX ix_ai_interactions_user_id   ON ai_interactions(user_id);
                    CREATE INDEX ix_ai_interactions_session   ON ai_interactions(session_id);
                    CREATE INDEX ix_ai_interactions_created   ON ai_interactions(created_at);
                """))
                conn.commit()
                logger.info("Table 'ai_interactions' created successfully.")

            # ── service_api_keys table ──────────────────────────────────────
            api_key_table = conn.execute(text(
                "SELECT to_regclass('public.service_api_keys');"
            )).scalar()
            if not api_key_table:
                logger.warning("Table 'service_api_keys' missing. Creating it...")
                conn.execute(text("""
                    CREATE TABLE service_api_keys (
                        id           UUID PRIMARY KEY,
                        service_name VARCHAR NOT NULL,
                        api_key_hash VARCHAR NOT NULL UNIQUE,
                        permissions  JSON NOT NULL,
                        allowed_ips  JSON,
                        is_active    BOOLEAN DEFAULT TRUE,
                        created_at   TIMESTAMPTZ DEFAULT NOW(),
                        last_used_at TIMESTAMPTZ
                    );
                    CREATE INDEX ix_service_api_keys_hash ON service_api_keys(api_key_hash);
                """))
                conn.commit()
                
                # Insert a default key for testing
                import uuid
                import secrets
                
                raw_key = f"ai_dev_{secrets.token_hex(16)}"
                conn.execute(text(f"""
                    INSERT INTO service_api_keys (id, service_name, api_key_hash, permissions, is_active)
                    VALUES ('{uuid.uuid4()}', 'Railway Auto-Generated', '{raw_key}', '["read:interactions", "read:places", "read:analytics", "read:training_data"]', true);
                """))
                conn.commit()
                
                logger.info("Table 'service_api_keys' created successfully.")
                logger.info(f"======> GENERATED DEFAULT AI API KEY: {raw_key} <======")

            # ── Add Social Auth columns to users table ────────────────────
            try:
                cols = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name='users';"
                )).fetchall()
                existing_cols = {row[0] for row in cols}
                
                if 'firebase_uid' not in existing_cols:
                    logger.info("Adding 'firebase_uid' column to users table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN firebase_uid VARCHAR UNIQUE;"))
                    conn.execute(text("CREATE INDEX ix_users_firebase_uid ON users(firebase_uid);"))
                    conn.commit()
                    
                if 'provider' not in existing_cols:
                    logger.info("Adding 'provider' column to users table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN provider VARCHAR DEFAULT 'local';"))
                    conn.commit()
                    
                if 'is_deleted' not in existing_cols:
                    logger.info("Adding 'is_deleted' column to users table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;"))
                    conn.commit()
                    
                if 'deleted_at' not in existing_cols:
                    logger.info("Adding 'deleted_at' column to users table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN deleted_at TIMESTAMPTZ;"))
                    conn.commit()
                    
                # Ensure password_hash is nullable (for social login)
                logger.info("Ensuring password_hash can be null for social logins...")
                conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;"))
                conn.commit()
                    
                logger.info("Users table columns check complete.")
            except Exception as col_err:
                logger.error(f"Error adding columns to users: {col_err}")

            # ── password_reset_tokens table ──────────────────────────────
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS password_reset_tokens (
                        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        token_hash    VARCHAR NOT NULL UNIQUE,
                        expires_at    TIMESTAMPTZ NOT NULL,
                        is_used       BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at    TIMESTAMPTZ DEFAULT NOW() NOT NULL
                    );
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_prt_user_id    ON password_reset_tokens(user_id);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_prt_token_hash ON password_reset_tokens(token_hash);"))
                conn.commit()
                logger.info("Table 'password_reset_tokens' ensured.")
            except Exception as prt_err:
                logger.error(f"Error creating password_reset_tokens: {prt_err}")
                conn.rollback()

            # ── property_favorites table ─────────────────────────────────
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS property_favorites (
                        id           SERIAL PRIMARY KEY,
                        user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        property_id  INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                        created_at   TIMESTAMPTZ DEFAULT NOW(),
                        updated_at   TIMESTAMPTZ,
                        CONSTRAINT unique_user_property_favorite UNIQUE (user_id, property_id)
                    );
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pf_user_id     ON property_favorites(user_id);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pf_property_id ON property_favorites(property_id);"))
                conn.commit()
                logger.info("Table 'property_favorites' ensured.")
            except Exception as pf_err:
                logger.error(f"Error creating property_favorites: {pf_err}")
                conn.rollback()

            # ── subcategories table ──────────────────────────────────────
            # ── subcategories table ──────────────────────────────────────
            try:
                # Ensure table exists first
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS subcategories (
                        id           SERIAL PRIMARY KEY,
                        name         VARCHAR(255) NOT NULL,
                        place_id     INTEGER NOT NULL REFERENCES places(id) ON DELETE CASCADE,
                        owner_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        is_deleted   BOOLEAN DEFAULT FALSE,
                        deleted_at   TIMESTAMPTZ,
                        created_at   TIMESTAMPTZ DEFAULT NOW(),
                        updated_at   TIMESTAMPTZ
                    );
                """))
                
                # Check columns for migration
                cols = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name='subcategories';"
                )).fetchall()
                existing_cols = {row[0] for row in cols}
                
                if 'place_id' not in existing_cols:
                    if 'category_id' in existing_cols:
                        logger.info("Migrating subcategories: renaming category_id to place_id and fixing foreign key...")
                        conn.execute(text("ALTER TABLE subcategories RENAME COLUMN category_id TO place_id;"))
                        # Drop the old constraint that points to 'categories' table
                        conn.execute(text("ALTER TABLE subcategories DROP CONSTRAINT IF EXISTS subcategories_category_id_fkey;"))
                        # Add new constraint pointing to 'places' table
                        conn.execute(text("ALTER TABLE subcategories ADD CONSTRAINT subcategories_place_id_fkey FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE;"))
                    else:
                        logger.info("Migrating subcategories: adding place_id column...")
                        conn.execute(text("ALTER TABLE subcategories ADD COLUMN place_id INTEGER REFERENCES places(id) ON DELETE CASCADE;"))
                
                # Create indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_subcategories_place_id ON subcategories(place_id);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_subcategories_owner_id ON subcategories(owner_id);"))

                # Cleanup: Remove image_url if it still exists
                conn.execute(text("ALTER TABLE subcategories DROP COLUMN IF EXISTS image_url;"))
                
                # Fix categories: Add created_at if missing
                conn.execute(text("ALTER TABLE categories ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();"))
                
                conn.commit()
                logger.info("Table 'subcategories' and 'categories' schema ensured.")
            except Exception as sub_err:
                logger.error(f"Error fixing subcategories/categories: {sub_err}")
                conn.rollback()

            # ── items table migration ────────────────────────────────────
            try:
                cols = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name='items';"
                )).fetchall()
                existing_cols = {row[0] for row in cols}

                if 'sub_category_id' not in existing_cols:
                    logger.info("Migrating 'items' table: adding sub_category_id...")
                    conn.execute(text("ALTER TABLE items ADD COLUMN sub_category_id INTEGER REFERENCES subcategories(id) ON DELETE CASCADE;"))
                    conn.commit()
                
                if 'image_url' not in existing_cols:
                    conn.execute(text("ALTER TABLE items ADD COLUMN image_url VARCHAR;"))
                    conn.commit()

                if 'is_available' not in existing_cols:
                    conn.execute(text("ALTER TABLE items ADD COLUMN is_available BOOLEAN DEFAULT TRUE;"))
                    conn.commit()
                
                if 'is_deleted' not in existing_cols:
                    conn.execute(text("ALTER TABLE items ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;"))
                    conn.commit()
                
                if 'deleted_at' not in existing_cols:
                    conn.execute(text("ALTER TABLE items ADD COLUMN deleted_at TIMESTAMPTZ;"))
                    conn.commit()

                if 'created_at' not in existing_cols:
                    conn.execute(text("ALTER TABLE items ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();"))
                    conn.commit()

                if 'updated_at' not in existing_cols:
                    conn.execute(text("ALTER TABLE items ADD COLUMN updated_at TIMESTAMPTZ;"))
                    conn.commit()

                # Fix legacy columns: make old NOT NULL columns nullable for new schema
                conn.execute(text("ALTER TABLE items DROP CONSTRAINT IF EXISTS items_place_id_fkey;"))
                conn.execute(text("ALTER TABLE items ALTER COLUMN place_id DROP NOT NULL;"))
                conn.execute(text("ALTER TABLE items ALTER COLUMN discount DROP NOT NULL;"))
                conn.execute(text("ALTER TABLE items ALTER COLUMN discount SET DEFAULT 0;"))
                conn.execute(text("ALTER TABLE items ALTER COLUMN is_active DROP NOT NULL;"))
                conn.execute(text("ALTER TABLE items ALTER COLUMN is_active SET DEFAULT TRUE;"))
                conn.commit()

                logger.info("Items table check complete.")
            except Exception as item_mig_err:
                logger.error(f"Error migrating items table: {item_mig_err}")
                conn.rollback()

        except Exception as e:
            logger.error(f"Startup migration failed: {e}")

# ─────────────────────────────────────────────
# RATE LIMITER
# ─────────────────────────────────────────────

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# ─────────────────────────────────────────────
# RESPONSE WRAPPER (optional)
# ─────────────────────────────────────────────

class ResponseWrapperMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        response = await call_next(request)

        if (
            response.status_code >= 400
            or request.url.path.startswith(
                ("/uploads", "/api/docs", "/api/openapi.json")
            )
        ):
            return response

        return response


# Uncomment if needed
# app.add_middleware(ResponseWrapperMiddleware)

# ─────────────────────────────────────────────
# EXCEPTION HANDLERS
# ─────────────────────────────────────────────

app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(PermissionError, permission_exception_handler)

# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins()
    if settings.ENVIRONMENT != "development"
    else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# STATIC FILES
from src.api.dashboard import owner_notifications, admin_notifications

# ─────────────────────────────────────────────

os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory=settings.UPLOAD_FOLDER),
    name="uploads"
)

# ─────────────────────────────────────────────
# ROUTERS
# ─────────────────────────────────────────────

# ─── MOBILE API ─────────────────────────────────────────────
app.include_router(mobile_auth.router, prefix="/api/mobile/auth", tags=["Mobile - Auth"])
app.include_router(mobile_places.router, prefix="/api/mobile/places", tags=["Mobile - Places"])
app.include_router(mobile_categories.router, prefix="/api/mobile/categories", tags=["Mobile - Categories"])
app.include_router(mobile_search.router, prefix="/api/mobile/search", tags=["Mobile - Search"])
app.include_router(mobile_favorites.router, prefix="/api/mobile/favorites", tags=["Mobile - Favorites"])
app.include_router(mobile_reviews.router, prefix="/api/mobile/reviews", tags=["Mobile - Reviews"])
app.include_router(mobile_items.router, prefix="/api/mobile/items", tags=["Mobile - Items"])
app.include_router(mobile_interactions.router, prefix="/api/mobile/interactions", tags=["Mobile - Interactions"])
app.include_router(mobile_recommendations.router, prefix="/api/mobile/recommendations", tags=["Mobile - Recommendations"])
app.include_router(mobile_properties.router, prefix="/api/mobile/properties", tags=["Mobile - Properties"])
app.include_router(mobile_notifications.router, prefix="/api/mobile/notifications", tags=["Mobile - Notifications"])
app.include_router(mobile_ai.router,            prefix="/api/mobile/ai",            tags=["Mobile - AI"])

# ─── DASHBOARD API ──────────────────────────────────────────
app.include_router(dashboard_places.router, prefix="/api/dashboard/places", tags=["Dashboard - Places"])
app.include_router(dashboard_items.router, prefix="/api/dashboard/items", tags=["Dashboard - Items"])
app.include_router(dashboard_upload.router, prefix="/api/dashboard/upload", tags=["Dashboard - Upload"])
app.include_router(dashboard_categories.router, prefix="/api/dashboard/categories", tags=["Dashboard - Categories"])
app.include_router(dashboard_admin.router, prefix="/api/dashboard/admin", tags=["Dashboard - Admin"])
app.include_router(admin_notifications.router, prefix="/api/dashboard/admin/notifications", tags=["Dashboard - Admin Notifications"])
app.include_router(dashboard_owner.router, prefix="/api/owner", tags=["Dashboard - Owner"])
app.include_router(owner_notifications.router, prefix="/api/owner/notifications", tags=["Dashboard - Owner Notifications"])

# ─── EXTERNAL API (AI GATEWAY) ──────────────────────────────────────────
from src.api.external import ai_data
app.include_router(ai_data.router, prefix="/api/v1")

# ─── MENU MANAGEMENT API ────────────────────────────────────
app.include_router(menu_categories.router, prefix="/api/v1")
app.include_router(menu_subcategories.router, prefix="/api/v1")
app.include_router(menu_items.router, prefix="/api/v1")

# ─────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────

@app.get("/api/health", tags=["Health"])
async def health(db=Depends(get_db)):

    from sqlalchemy import text
    import httpx
    import redis

    health_status = {
        "status": "healthy",
        "services": {
            "database": "unhealthy",
            "redis": "disabled",
            "ai_service": "unhealthy"
        }
    }

    # DATABASE CHECK
    try:
        db.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        logger.error(f"Database health failed: {e}")

    # REDIS CHECK
    if settings.ENABLE_REDIS:

        try:
            r = redis.from_url(settings.REDIS_URL, socket_timeout=2)

            if r.ping():
                health_status["services"]["redis"] = "healthy"

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["services"]["redis"] = "unhealthy"
            logger.error(f"Redis health failed: {e}")

    # AI SERVICE CHECK
    try:

        async with httpx.AsyncClient(timeout=2.0) as client:

            resp = await client.get(
                f"{settings.AI_SERVICE_URL}/health"
            )

            if resp.status_code == 200:
                health_status["services"]["ai_service"] = "healthy"

    except Exception:
        health_status["services"]["ai_service"] = "unhealthy"

    if health_status["status"] != "healthy":

        return JSONResponse(
            status_code=503,
            content=health_status
        )

    return health_status


# ─────────────────────────────────────────────
# LOCAL DEV ONLY
# ─────────────────────────────────────────────

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )