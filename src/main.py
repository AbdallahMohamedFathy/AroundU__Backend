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
from src.api.v1 import auth
from src.api.v1 import places
from src.api.v1 import reviews
from src.api.v1 import chat
from src.api.v1 import categories
from src.api.v1 import search
from src.api.v1 import favorites
from src.api.v1 import upload

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
    rate_limit_handler
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

_p = settings.API_V1_STR

app.include_router(auth.router, prefix=f"{_p}/auth", tags=["Auth"])
app.include_router(categories.router, prefix=f"{_p}/categories", tags=["Categories"])
app.include_router(places.router, prefix=f"{_p}/places", tags=["Places"])
app.include_router(search.router, prefix=f"{_p}/search", tags=["Search"])
app.include_router(chat.router, prefix=f"{_p}/chat", tags=["Chat"])
app.include_router(favorites.router, prefix=f"{_p}/favorites", tags=["Favorites"])
app.include_router(reviews.router, prefix=f"{_p}/reviews", tags=["Reviews"])
app.include_router(upload.router, prefix=f"{_p}/upload", tags=["Upload"])

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