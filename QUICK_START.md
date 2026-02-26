# AroundU Backend - Quick Start Guide

## What's Been Done

I've implemented a comprehensive enhancement to your AroundU backend with the following features:

### ✅ Completed Components

#### 1. **Configuration & Environment** (.env.example, enhanced config.py)
- Complete environment variable setup
- Security, email, file upload, Redis, pagination settings
- CORS and rate limiting configuration

#### 2. **Database Models** (3 new models + 5 enhanced)
**New:**
- `Favorite` - User bookmarks
- `Review` - Ratings and comments
- `PlaceImage` - Multiple images per place

**Enhanced:**
- `User` - Added roles, verification, password reset
- `Place` - Added address, phone, website, active status
- `SearchHistory` - Added relationship
- `ChatMessage` - Added relationship

#### 3. **Pydantic Schemas** (Complete validation layer)
- User (create, update, password change, reset)
- Places (create, update, list with pagination)
- Reviews, Favorites, Images
- All with proper validation

#### 4. **Utility Modules** (4 new utility files)
- `distance.py` - Haversine formula for location calculations
- `email.py` - Email verification and password reset
- `file_upload.py` - Image upload with validation
- `pagination.py` - Standardized pagination

#### 5. **Service Layer** (2 new services)
- `favorite_service.py` - Complete favorite management
- `review_service.py` - Complete review system with rating recalculation

#### 6. **Dependencies** (Updated requirements)
- Added all necessary packages for new features
- Created requirements-dev.txt for development tools

---

## What Still Needs Implementation

### High Priority

1. **Database Migration**
   ```bash
   alembic revision --autogenerate -m "Add favorites, reviews, place images, and user enhancements"
   alembic upgrade head
   ```

2. **Update Existing Services**
   - `place_service.py` - Add get by ID, update, delete, location search
   - `auth_service.py` - Add email verification, password reset
   - `user_service.py` - Add profile update, password change

3. **Create API Endpoints**
   - `api/v1/favorites.py` - Favorites endpoints
   - `api/v1/reviews.py` - Review endpoints
   - `api/v1/upload.py` - Image upload endpoint
   - Update `api/v1/places.py` - Add CRUD and location search
   - Update `api/v1/auth.py` - Add profile update, password reset

4. **Add Middleware**
   - Rate limiting
   - Logging
   - Error handling

### Medium Priority

5. **Testing**
   - Create test suite
   - Add fixtures
   - Test all endpoints

6. **Seed Data**
   - Create seed script
   - Add sample data

7. **Docker**
   - Dockerfile
   - docker-compose.yml

### Low Priority

8. **Admin Panel**
   - Role-based access control
   - Admin-only endpoints

9. **Redis Caching**
   - Cache frequently accessed data
   - Session management

10. **Documentation**
    - Complete API docs
    - Deployment guide

---

## Installation & Setup

### 1. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Or install with development tools
pip install -r requirements-dev.txt
```

### 2. Configure Environment

```bash
# Copy the environment template
cp .env.example .env

# Edit .env and set your values:
# - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
# - DATABASE_URL (if using PostgreSQL)
# - SMTP settings (if you want email functionality)
```

### 3. Create Uploads Directory

```bash
mkdir uploads
mkdir uploads/places
```

### 4. Run Database Migrations

```bash
# Generate migration for new models
alembic revision --autogenerate -m "Add new features"

# Apply migrations
alembic upgrade head
```

### 5. Start the Server

```bash
uvicorn src.main:app --reload
```

Visit http://localhost:8000/docs for API documentation

---

## Next Implementation Steps (In Order)

### Step 1: Create Migration

Run this command to create a migration for all the new database models:

```bash
alembic revision --autogenerate -m "Add favorites, reviews, place images and enhanced user/place models"
alembic upgrade head
```

### Step 2: Update Place Service

Add to `src/services/place_service.py`:

```python
from src.utils.distance import calculate_distance
from src.utils.pagination import paginate
from typing import Optional

def get_place_by_id(db: Session, place_id: int) -> Place:
    place = db.execute(select(Place).filter(Place.id == place_id)).scalar_one_or_none()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place

def update_place(db: Session, place_id: int, place_data: PlaceUpdate) -> Place:
    place = get_place_by_id(db, place_id)

    for key, value in place_data.dict(exclude_unset=True).items():
        setattr(place, key, value)

    db.commit()
    db.refresh(place)
    return place

def delete_place(db: Session, place_id: int) -> bool:
    place = get_place_by_id(db, place_id)
    db.delete(place)
    db.commit()
    return True

def search_places_nearby(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    category_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20
):
    query = db.query(Place).filter(Place.is_active == True)

    if category_id:
        query = query.filter(Place.category_id == category_id)

    places = query.all()

    # Filter by distance and add distance field
    places_with_distance = []
    for place in places:
        distance = calculate_distance(latitude, longitude, place.latitude, place.longitude)
        if distance <= radius_km:
            place.distance_km = distance
            places_with_distance.append(place)

    # Sort by distance
    places_with_distance.sort(key=lambda p: p.distance_km)

    # Paginate results
    start = (page - 1) * page_size
    end = start + page_size
    total = len(places_with_distance)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "items": places_with_distance[start:end]
    }
```

### Step 3: Create Favorites API

Create `src/api/v1/favorites.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.core.database import get_db
from src.api.v1.auth import get_current_user
from src.models.user import User
from src.schemas.favorite import FavoriteCreate, FavoriteResponse
from src.services.favorite_service import add_favorite, get_user_favorites, remove_favorite

router = APIRouter()

@router.post("/", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
def create_favorite(
    favorite_data: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return add_favorite(db, current_user.id, favorite_data)

@router.get("/", response_model=List[FavoriteResponse])
def list_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_user_favorites(db, current_user.id)

@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_favorite(
    place_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    remove_favorite(db, current_user.id, place_id)
```

### Step 4: Create Reviews API

Create `src/api/v1/reviews.py`:

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.api.v1.auth import get_current_user
from src.models.user import User
from src.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from src.services.review_service import (
    create_review, get_place_reviews, update_review, delete_review
)

router = APIRouter()

@router.post("/", response_model=ReviewResponse, status_code=201)
def create_place_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_review(db, current_user.id, review_data)

@router.get("/place/{place_id}")
def get_reviews_for_place(
    place_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return get_place_reviews(db, place_id, page, page_size)

@router.put("/{review_id}", response_model=ReviewResponse)
def update_place_review(
    review_id: int,
    review_data: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_review(db, review_id, current_user.id, review_data)

@router.delete("/{review_id}", status_code=204)
def delete_place_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    delete_review(db, review_id, current_user.id)
```

### Step 5: Create Image Upload API

Create `src/api/v1/upload.py`:

```python
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.api.v1.auth import get_current_user
from src.models.user import User
from src.models.place_image import PlaceImage
from src.schemas.place_image import PlaceImageResponse
from src.utils.file_upload import save_upload_file

router = APIRouter()

@router.post("/place-image", response_model=PlaceImageResponse)
async def upload_place_image(
    place_id: int = Form(...),
    is_primary: bool = Form(False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Save file
    file_path = await save_upload_file(file, subfolder="places")

    # Create database record
    db_image = PlaceImage(
        place_id=place_id,
        image_url=f"/uploads/{file_path}",
        is_primary=is_primary
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)

    return db_image
```

### Step 6: Register New Routers

Update `src/main.py`:

```python
from src.api.v1 import favorites, reviews, upload

# Add these lines after existing router includes
app.include_router(favorites.router, prefix=f"{settings.API_V1_STR}/favorites", tags=["favorites"])
app.include_router(reviews.router, prefix=f"{settings.API_V1_STR}/reviews", tags=["reviews"])
app.include_router(upload.router, prefix=f"{settings.API_V1_STR}/upload", tags=["upload"])

# Add static files for uploads
from fastapi.staticfiles import StaticFiles
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
```

### Step 7: Test the New Features

```bash
# Start the server
uvicorn src.main:app --reload

# Visit Swagger UI
# http://localhost:8000/docs

# Test the new endpoints:
# 1. POST /api/favorites - Add a favorite
# 2. GET /api/favorites - List favorites
# 3. POST /api/reviews - Create a review
# 4. GET /api/reviews/place/1 - Get reviews for a place
# 5. POST /api/upload/place-image - Upload an image
```

---

## File Structure Summary

```
📦 AroundU_Backend
├── 📄 .env.example                    ✅ NEW - Environment template
├── 📄 requirements.txt                ✅ UPDATED - Added new dependencies
├── 📄 requirements-dev.txt            ✅ NEW - Development dependencies
├── 📄 IMPLEMENTATION_GUIDE.md         ✅ NEW - Complete guide
├── 📄 QUICK_START.md                  ✅ NEW - This file
├── 📂 src/
│   ├── 📄 main.py                     ⏳ Update to add new routers
│   ├── 📂 core/
│   │   └── 📄 config.py               ✅ UPDATED - Complete settings
│   ├── 📂 models/
│   │   ├── 📄 user.py                 ✅ UPDATED - Roles, verification
│   │   ├── 📄 place.py                ✅ UPDATED - Enhanced fields
│   │   ├── 📄 favorite.py             ✅ NEW
│   │   ├── 📄 review.py               ✅ NEW
│   │   ├── 📄 place_image.py          ✅ NEW
│   │   ├── 📄 search_history.py       ✅ UPDATED
│   │   └── 📄 chat_message.py         ✅ UPDATED
│   ├── 📂 schemas/
│   │   ├── 📄 user.py                 ✅ UPDATED
│   │   ├── 📄 place.py                ✅ UPDATED
│   │   ├── 📄 favorite.py             ✅ NEW
│   │   ├── 📄 review.py               ✅ NEW
│   │   └── 📄 place_image.py          ✅ NEW
│   ├── 📂 services/
│   │   ├── 📄 favorite_service.py     ✅ NEW - Complete
│   │   ├── 📄 review_service.py       ✅ NEW - Complete
│   │   ├── 📄 place_service.py        ⏳ Update needed
│   │   ├── 📄 auth_service.py         ⏳ Update needed
│   │   └── 📄 user_service.py         ⏳ Update needed
│   ├── 📂 api/v1/
│   │   ├── 📄 favorites.py            ❌ Create this
│   │   ├── 📄 reviews.py              ❌ Create this
│   │   ├── 📄 upload.py               ❌ Create this
│   │   ├── 📄 places.py               ⏳ Update needed
│   │   └── 📄 auth.py                 ⏳ Update needed
│   └── 📂 utils/                      ✅ NEW
│       ├── 📄 distance.py             ✅ NEW
│       ├── 📄 email.py                ✅ NEW
│       ├── 📄 file_upload.py          ✅ NEW
│       └── 📄 pagination.py           ✅ NEW
└── 📂 uploads/                        ❌ Create directory
    └── 📂 places/                     ❌ Create directory
```

---

## Common Issues & Solutions

### Issue: Import Errors
**Solution:** Make sure all `__init__.py` files are updated with new imports

### Issue: Migration Fails
**Solution:**
```bash
# Delete existing migrations and recreate
alembic downgrade base
alembic revision --autogenerate -m "Fresh start"
alembic upgrade head
```

### Issue: Pydantic Version Conflict
**Solution:** The updated requirements.txt uses Pydantic 2.x. If you need Pydantic 1.x:
```bash
pip install "pydantic<2.0"
```

### Issue: Image Upload Fails
**Solution:** Ensure uploads directory exists:
```bash
mkdir -p uploads/places
chmod 755 uploads
```

---

## Testing the Implementation

### 1. Test Favorites

```bash
# Add favorite
curl -X POST http://localhost:8000/api/favorites \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"place_id": 1}'

# List favorites
curl -X GET http://localhost:8000/api/favorites \
  -H "Authorization: Bearer <token>"

# Remove favorite
curl -X DELETE http://localhost:8000/api/favorites/1 \
  -H "Authorization: Bearer <token>"
```

### 2. Test Reviews

```bash
# Create review
curl -X POST http://localhost:8000/api/reviews \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"place_id": 1, "rating": 5, "comment": "Amazing place!"}'

# Get place reviews
curl -X GET http://localhost:8000/api/reviews/place/1
```

### 3. Test Image Upload

```bash
# Upload image
curl -X POST http://localhost:8000/api/upload/place-image \
  -H "Authorization: Bearer <token>" \
  -F "place_id=1" \
  -F "is_primary=true" \
  -F "file=@/path/to/image.jpg"
```

---

## Summary

### What You Got

1. ✅ **Enhanced database models** with 3 new tables
2. ✅ **Complete validation layer** with Pydantic schemas
3. ✅ **Utility functions** for distance, email, file upload, pagination
4. ✅ **Service layer** for favorites and reviews
5. ✅ **Updated dependencies** with all required packages
6. ✅ **Comprehensive documentation**

### What You Need to Do

1. Run database migrations
2. Create 3 new API endpoint files (favorites, reviews, upload)
3. Update 2 existing services (place, auth, user)
4. Update 2 existing API files (places, auth)
5. Update main.py to register new routers
6. Create uploads directory
7. Test everything

### Estimated Time

- **Migrations**: 5 minutes
- **API endpoints**: 30-45 minutes
- **Service updates**: 30-45 minutes
- **Testing**: 30 minutes
- **Total**: ~2 hours

---

## Need Help?

Refer to:
- `IMPLEMENTATION_GUIDE.md` - Detailed technical documentation
- `src/services/favorite_service.py` - Example service implementation
- `src/services/review_service.py` - Another example with complex logic
- Swagger UI at `/docs` - Interactive API testing

All code follows FastAPI best practices and includes proper error handling, validation, and documentation.
