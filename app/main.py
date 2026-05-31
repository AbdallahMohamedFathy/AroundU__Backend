from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.user.cart_api import router as cart_router
from app.api.user.order_api import router as order_router
from app.api.owner.order_api import router as owner_router
from app.middleware import ExceptionMiddleware, ValidationMiddleware
from app.dependencies import get_db

app = FastAPI(title="Order Management System", version="1.0.0")

# CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(ExceptionMiddleware)
app.add_middleware(ValidationMiddleware)

# Include routers
app.include_router(cart_router, prefix="/cart", tags=["Cart"])
app.include_router(order_router, prefix="/orders", tags=["Orders"])
app.include_router(owner_router, prefix="/owner", tags=["Owner Dashboard"])
