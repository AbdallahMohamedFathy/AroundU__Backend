# AroundU Backend - Complete Implementation Guide

## Table of Contents
1. [Overview](#overview)
2. [What Has Been Implemented](#what-has-been-implemented)
3. [Project Structure](#project-structure)
4. [Setup Instructions](#setup-instructions)
5. [Next Steps](#next-steps)
6. [API Documentation](#api-documentation)
7. [Database Schema](#database-schema)
8. [Testing](#testing)
9. [Deployment](#deployment)

---

## Overview

AroundU is a comprehensive location-based service backend built with FastAPI. This implementation includes:
- User authentication with JWT
- Location-based place discovery
- Reviews and ratings system
- User favorites
- Image upload for places
- Search with history tracking
- AI chat assistant
- Admin panel with role-based access
- Rate limiting and security features

---

## What Has Been Implemented

### ✅ Completed

#### 1. Configuration & Environment
- **`.env.example`**: Complete environment variable template
- **Enhanced `config.py`**:
  - Security settings (JWT, secrets)
  - Email configuration (SMTP)
  - File upload settings
  - Redis configuration
  - Pagination settings
  - CORS configuration
  - Location search settings

#### 2. Database Models (Enhanced)
All models now include:
- Proper relationships with cascade deletes
- Timestamps (created_at, updated_at)
- Data validation constraints
- Indexes for performance

**New Models:**
- `User` (enhanced with role, verification, password reset)
- `Place` (enhanced with address, phone, website, active status)
- `Favorite` (user favorites/bookmarks)
- `Review` (user reviews with ratings)
- `PlaceImage` (multiple images per place)

**Updated Models:**
- `SearchHistory` (with user relationship)
- `ChatMessage` (with user relationship)

#### 3. Pydantic Schemas
Complete validation schemas for:
- User management (create, update, password change, reset)
- Places (create, update, list with pagination)
- Reviews (create, update, with user info)
- Favorites (create, list with place details)
- Images (upload, manage)

#### 4. Utility Modules
- **`distance.py`**: Haversine formula for location calculations
- **`email.py`**: Email verification and password reset
- **`file_upload.py`**: Image upload with validation
- **`pagination.py`**: Standardized pagination

#### 5. Requirements
- Updated `requirements.txt` with all dependencies
- Created `requirements-dev.txt` for development tools

---

## Project Structure

```
AroundU_Backend/
├── .env.example                 # Environment variables template
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── alembic/                     # Database migrations
│   ├── versions/                # Migration files
│   └── env.py
├── src/
│   ├── main.py                  # FastAPI application entry
│   ├── core/
│   │   ├── config.py            # ✅ Enhanced settings
│   │   ├── database.py          # Database connection
│   │   └── security.py          # Auth utilities
│   ├── models/                  # ✅ All updated
│   │   ├── user.py              # ✅ Enhanced with roles
│   │   ├── place.py             # ✅ Enhanced with details
│   │   ├── category.py
│   │   ├── favorite.py          # ✅ NEW
│   │   ├── review.py            # ✅ NEW
│   │   ├── place_image.py       # ✅ NEW
│   │   ├── search_history.py    # ✅ Updated
│   │   └── chat_message.py      # ✅ Updated
│   ├── schemas/                 # ✅ All complete
│   │   ├── user.py              # ✅ Enhanced
│   │   ├── place.py             # ✅ Enhanced
│   │   ├── favorite.py          # ✅ NEW
│   │   ├── review.py            # ✅ NEW
│   │   ├── place_image.py       # ✅ NEW
│   │   ├── category.py
│   │   ├── search.py
│   │   └── chat.py
│   ├── services/                # ⏳ Needs updates
│   │   ├── auth_service.py      # ⏳ Add password reset, verification
│   │   ├── user_service.py      # ⏳ Add profile update
│   │   ├── place_service.py     # ⏳ Add CRUD, location search
│   │   ├── favorite_service.py  # ❌ TO BE CREATED
│   │   ├── review_service.py    # ❌ TO BE CREATED
│   │   ├── search_service.py    # ⏳ Add location filtering
│   │   └── chat_service.py
│   ├── api/v1/                  # ⏳ Needs updates
│   │   ├── auth.py              # ⏳ Add password reset, verification
│   │   ├── places.py            # ⏳ Add full CRUD, location search
│   │   ├── favorites.py         # ❌ TO BE CREATED
│   │   ├── reviews.py           # ❌ TO BE CREATED
│   │   ├── upload.py            # ❌ TO BE CREATED
│   │   ├── categories.py
│   │   ├── search.py
│   │   └── chat.py
│   └── utils/                   # ✅ NEW
│       ├── distance.py          # ✅ Location calculations
│       ├── email.py             # ✅ Email sending
│       ├── file_upload.py       # ✅ Image handling
│       └── pagination.py        # ✅ Pagination helper
├── uploads/                     # Image uploads directory
├── tests/                       # ❌ TO BE CREATED
│   ├── test_auth.py
│   ├── test_places.py
│   ├── test_favorites.py
│   └── test_reviews.py
├── scripts/                     # ❌ TO BE CREATED
│   ├── seed_data.py
│   └── reset_db.py
└── docs/                        # ⏳ Partially complete
    ├── API.md
    └── DEPLOYMENT.md
```

**Legend:**
- ✅ Complete
- ⏳ Needs updates
- ❌ To be created

---

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- PostgreSQL (for production) or SQLite (for development)
- Redis (optional, for caching)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd AroundU_Backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For development:
pip install -r requirements-dev.txt
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and fill in your values
# At minimum, set:
# - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
# - DATABASE_URL (if using PostgreSQL)
# - SMTP settings (if using email features)
```

### 4. Database Setup

```bash
# Create uploads directory
mkdir uploads

# Run migrations
alembic upgrade head

# (Optional) Seed database with test data
python scripts/seed_data.py
```

### 5. Run the Application

```bash
# Development
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. Access API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Next Steps

### Immediate Priorities (Required for Basic Functionality)

#### 1. Create Database Migration
```bash
alembic revision --autogenerate -m "Add favorites, reviews, and place images"
alembic upgrade head
```

#### 2. Implement Services (in this order)

**A. `favorite_service.py`** - User favorites management
**B. `review_service.py`** - Reviews and ratings
**C. Update `place_service.py`** - Add:
  - Get place by ID
  - Update place
  - Delete place
  - Location-based search
  - Calculate average ratings

**D. Update `auth_service.py`** - Add:
  - Email verification
  - Password reset request
  - Password reset confirmation
  - Token refresh

**E. Update `user_service.py`** - Add:
  - Profile update
  - Password change

#### 3. Implement API Endpoints

**A. `favorites.py`** - Favorite endpoints
```python
POST   /api/favorites              # Add favorite
GET    /api/favorites              # List user's favorites
DELETE /api/favorites/{place_id}  # Remove favorite
```

**B. `reviews.py`** - Review endpoints
```python
POST   /api/reviews              # Create review
GET    /api/reviews/place/{id}   # Get place reviews
PUT    /api/reviews/{id}         # Update own review
DELETE /api/reviews/{id}         # Delete own review
```

**C. `upload.py`** - File upload
```python
POST   /api/upload/place-image   # Upload place image
DELETE /api/upload/image/{id}    # Delete image
```

**D. Update `places.py`** - Add:
```python
GET    /api/places/{id}          # Get single place
PUT    /api/places/{id}          # Update place
DELETE /api/places/{id}          # Delete place
GET    /api/places/nearby        # Location-based search
```

**E. Update `auth.py`** - Add:
```python
PUT    /api/auth/profile         # Update profile
POST   /api/auth/change-password # Change password
POST   /api/auth/forgot-password # Request reset
POST   /api/auth/reset-password  # Reset password
GET    /api/auth/verify/{token}  # Verify email
POST   /api/auth/refresh         # Refresh token
```

#### 4. Add Rate Limiting & Security

Create `src/core/rate_limit.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

Apply to routes:
```python
@router.post("/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

#### 5. Add Logging

Create `src/core/logging_config.py`:
```python
import logging
from pythonjsonlogger import jsonlogger

def setup_logging():
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter()
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
```

#### 6. Create Tests

Create `tests/test_places.py`:
```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_get_places():
    response = client.get("/api/places")
    assert response.status_code == 200
    assert "items" in response.json()

def test_create_place():
    place_data = {
        "name": "Test Place",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "category_id": 1
    }
    response = client.post("/api/places", json=place_data)
    assert response.status_code == 201
```

#### 7. Create Seed Data Script

Create `scripts/seed_data.py`:
```python
from src.core.database import SessionLocal
from src.models import Category, Place, User

def seed_database():
    db = SessionLocal()

    # Create categories
    categories = [
        Category(name="Restaurant", icon="🍽️"),
        Category(name="Cafe", icon="☕"),
        Category(name="Park", icon="🌳"),
    ]
    db.add_all(categories)
    db.commit()

    # Create sample places
    places = [
        Place(
            name="Central Perk",
            description="Famous coffee shop",
            latitude=40.7128,
            longitude=-74.0060,
            category_id=2
        ),
    ]
    db.add_all(places)
    db.commit()

if __name__ == "__main__":
    seed_database()
```

#### 8. Add Docker Support

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/aroundu
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: aroundu
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## API Documentation

### Authentication Endpoints

#### Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "full_name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Places Endpoints

#### List Places (with pagination and location)
```http
GET /api/places?page=1&page_size=20&latitude=40.7128&longitude=-74.0060&radius=5
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5,
  "items": [
    {
      "id": 1,
      "name": "Central Perk",
      "description": "Famous coffee shop",
      "address": "123 Main St",
      "phone": "+1-555-1234",
      "website": "https://centralperk.com",
      "rating": 4.5,
      "review_count": 120,
      "latitude": 40.7128,
      "longitude": -74.0060,
      "category_id": 2,
      "distance_km": 0.5,
      "is_favorited": true,
      "images": [
        {
          "id": 1,
          "image_url": "/uploads/places/abc123.jpg",
          "is_primary": true
        }
      ]
    }
  ]
}
```

#### Get Single Place
```http
GET /api/places/1
Authorization: Bearer <token>
```

#### Create Place
```http
POST /api/places
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "New Restaurant",
  "description": "Amazing food",
  "address": "456 Oak Ave",
  "phone": "+1-555-5678",
  "website": "https://example.com",
  "latitude": 40.7589,
  "longitude": -73.9851,
  "category_id": 1
}
```

#### Update Place
```http
PUT /api/places/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

#### Delete Place
```http
DELETE /api/places/1
Authorization: Bearer <token>
```

### Favorites Endpoints

#### Add Favorite
```http
POST /api/favorites
Authorization: Bearer <token>
Content-Type: application/json

{
  "place_id": 1
}
```

#### List Favorites
```http
GET /api/favorites
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "place_id": 1,
    "created_at": "2024-01-01T00:00:00Z",
    "place": {
      "id": 1,
      "name": "Central Perk",
      "rating": 4.5,
      "latitude": 40.7128,
      "longitude": -74.0060
    }
  }
]
```

#### Remove Favorite
```http
DELETE /api/favorites/1
Authorization: Bearer <token>
```

### Reviews Endpoints

#### Create Review
```http
POST /api/reviews
Authorization: Bearer <token>
Content-Type: application/json

{
  "place_id": 1,
  "rating": 5,
  "comment": "Amazing place!"
}
```

#### Get Place Reviews
```http
GET /api/reviews/place/1?page=1&page_size=10
```

**Response:**
```json
{
  "total": 50,
  "page": 1,
  "page_size": 10,
  "total_pages": 5,
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "user_name": "John Doe",
      "place_id": 1,
      "rating": 5,
      "comment": "Amazing place!",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": null
    }
  ]
}
```

#### Update Review
```http
PUT /api/reviews/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "rating": 4,
  "comment": "Good, but not perfect"
}
```

#### Delete Review
```http
DELETE /api/reviews/1
Authorization: Bearer <token>
```

### Image Upload

#### Upload Place Image
```http
POST /api/upload/place-image
Authorization: Bearer <token>
Content-Type: multipart/form-data

place_id: 1
file: <image file>
is_primary: true
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐
│    users    │
├─────────────┤
│ id          │──┐
│ full_name   │  │
│ email       │  │
│ password... │  │
│ role        │  │
│ is_active   │  │
│ is_verified │  │
└─────────────┘  │
                 │
        ┌────────┴────────┐
        │                 │
┌───────▼────────┐ ┌─────▼──────┐
│   favorites    │ │  reviews   │
├────────────────┤ ├────────────┤
│ id             │ │ id         │
│ user_id     FK │ │ user_id FK │
│ place_id    FK │ │ place_id FK│
│ created_at     │ │ rating     │
└────────────────┘ │ comment    │
                   └────────────┘
                         │
         ┌───────────────┴──────────────┐
         │                              │
┌────────▼─────────┐          ┌─────────▼────────┐
│     places       │          │  place_images    │
├──────────────────┤          ├──────────────────┤
│ id               │──────────│ id               │
│ name             │          │ place_id      FK │
│ description      │          │ image_url        │
│ address          │          │ is_primary       │
│ phone            │          └──────────────────┘
│ website          │
│ rating           │
│ review_count     │
│ latitude         │
│ longitude        │
│ category_id   FK │
│ is_active        │
└──────────────────┘
         │
         │
┌────────▼──────┐
│  categories   │
├───────────────┤
│ id            │
│ name          │
│ icon          │
└───────────────┘
```

### Key Constraints

1. **User Uniqueness**: Email must be unique
2. **Favorite Uniqueness**: User can favorite a place only once
3. **Coordinate Validation**:
   - Latitude: -90 to 90
   - Longitude: -180 to 180
4. **Rating Validation**:
   - Place rating: 0 to 5
   - Review rating: 1 to 5
5. **Cascade Deletes**: When user/place deleted, related records are deleted

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_places.py

# Run with verbose output
pytest -v
```

### Test Structure

```python
# tests/conftest.py - Shared fixtures
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app
from src.core.database import Base, get_db

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///./test.db")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    # Create test user and return auth headers
    user_data = {
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "testpass123"
    }
    client.post("/api/auth/register", json=user_data)

    login_response = client.post("/api/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    token = login_response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
```

---

## Deployment

### Production Checklist

- [ ] Set strong `SECRET_KEY` in environment
- [ ] Configure production database (PostgreSQL)
- [ ] Set up Redis for caching
- [ ] Configure SMTP for emails
- [ ] Set `CORS_ORIGINS` to specific domains
- [ ] Enable HTTPS
- [ ] Set up error monitoring (Sentry)
- [ ] Configure logging to file/service
- [ ] Set up database backups
- [ ] Configure CDN for uploaded images
- [ ] Set rate limits appropriately
- [ ] Enable database connection pooling
- [ ] Set up health check endpoint
- [ ] Configure firewall rules
- [ ] Set up CI/CD pipeline

### Deployment with Docker

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f api

# Run migrations
docker-compose exec api alembic upgrade head

# Seed database
docker-compose exec api python scripts/seed_data.py
```

### Environment Variables for Production

```bash
# Application
ENVIRONMENT=production
SECRET_KEY=<generate-secure-key>

# Database
DATABASE_URL=postgresql://user:password@hostname:5432/aroundu

# Redis
REDIS_URL=redis://hostname:6379/0
ENABLE_REDIS=true

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<sendgrid-api-key>

# CORS
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# File Upload
UPLOAD_FOLDER=/var/www/uploads
MAX_UPLOAD_SIZE=10485760  # 10MB

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Logging
LOG_LEVEL=WARNING
```

---

## Support & Contributing

For issues and feature requests, please open an issue on GitHub.

For questions, contact: support@aroundu.com

---

## License

MIT License - See LICENSE file for details
