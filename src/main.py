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
from src.api.mobile import chat as mobile_chat
from src.api.mobile import categories as mobile_categories
from src.api.mobile import search as mobile_search
from src.api.mobile import favorites as mobile_favorites
from src.api.mobile import items as mobile_items

from src.api.dashboard import places as dashboard_places
from src.api.dashboard import items as dashboard_items
from src.api.dashboard import upload as dashboard_upload
from src.api.dashboard import categories as dashboard_categories
from src.api.dashboard import admin as dashboard_admin
from src.api.dashboard import owner as dashboard_owner

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
app.include_router(mobile_chat.router, prefix="/api/mobile/chat", tags=["Mobile - Chat"])
app.include_router(mobile_favorites.router, prefix="/api/mobile/favorites", tags=["Mobile - Favorites"])
app.include_router(mobile_reviews.router, prefix="/api/mobile/reviews", tags=["Mobile - Reviews"])
app.include_router(mobile_items.router, prefix="/api/mobile/items", tags=["Mobile - Items"])

# ─── DASHBOARD API ──────────────────────────────────────────
app.include_router(dashboard_places.router, prefix="/api/dashboard/places", tags=["Dashboard - Places"])
app.include_router(dashboard_items.router, prefix="/api/dashboard/items", tags=["Dashboard - Items"])
app.include_router(dashboard_upload.router, prefix="/api/dashboard/upload", tags=["Dashboard - Upload"])
app.include_router(dashboard_categories.router, prefix="/api/dashboard/categories", tags=["Dashboard - Categories"])
app.include_router(dashboard_admin.router, prefix="/api/dashboard/admin", tags=["Dashboard - Admin"])
app.include_router(dashboard_owner.router, prefix="/api/owner", tags=["Dashboard - Owner"])

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