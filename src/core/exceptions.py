from typing import Any, Optional, Union
from fastapi import Request, status, HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.core.logger import logger

class APIException(Exception):
    """Base class for all API exceptions."""
    def __init__(
        self, 
        message: str, 
        code: int = status.HTTP_400_BAD_REQUEST,
        data: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)

async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom APIException."""
    logger.error(f"API Error: {exc.message}", extra={"code": exc.code, "path": request.url.path})
    return JSONResponse(
        status_code=exc.code,
        content={
            "success": False,
            "data": exc.data,
            "error": {
                "message": exc.message,
                "code": exc.code
            }
        }
    )

async def http_exception_handler(request: Request, exc: Union[FastAPIHTTPException, StarletteHTTPException]):
    """Handle standard FastAPI/Starlette HTTPExceptions while preserving status codes."""
    logger.error(f"HTTP Error: {exc.detail}", extra={"code": exc.status_code, "path": request.url.path})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "message": str(exc.detail),
                "code": exc.status_code
            }
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors."""
    logger.warning("Validation Error", extra={"errors": exc.errors(), "path": request.url.path})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": None,
            "error": {
                "message": "Validation Error",
                "details": exc.errors(),
                "code": status.HTTP_422_UNPROCESSABLE_ENTITY
            }
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions."""
    logger.exception(f"Unhandled Exception: {str(exc)}", extra={"path": request.url.path})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": {
                "message": "Internal Server Error",
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
        }
    )

async def permission_exception_handler(request: Request, exc: PermissionError):
    """Handle standard Python PermissionError consistently."""
    logger.warning(f"Permission Denied: {str(exc)}", extra={"path": request.url.path})
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "success": False,
            "data": None,
            "error": {
                "message": str(exc),
                "code": status.HTTP_403_FORBIDDEN
            }
        }
    )

from slowapi.errors import RateLimitExceeded

async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle 429 Too Many Requests errors."""
    logger.warning(f"Rate Limit Exceeded for path: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "data": None,
            "error": {
                "message": "Rate Limit Exceeded. Please slow down.",
                "code": status.HTTP_429_TOO_MANY_REQUESTS
            }
        }
    )
