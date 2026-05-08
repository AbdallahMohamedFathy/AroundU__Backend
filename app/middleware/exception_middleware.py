from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.exception("Unhandled exception: %s", exc)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"},
            )
