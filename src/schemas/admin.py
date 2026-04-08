from pydantic import BaseModel

class UserPromotion(BaseModel):
    role: str # ADMIN, OWNER, USER

class PlaceCreateWithOwner(BaseModel):
    place_name: str
    description: str = None
    category_id: int
    location_link: str = None
    latitude: float = None
    longitude: float = None
    owner_email: str
    owner_password: str

class PlaceCreationResponse(BaseModel):
    place_id: int
    owner_id: int
    owner_email: str


class PropertyCreationResponse(BaseModel):
    property_id: int
    owner_id: int
    owner_email: str


class PropertyCreateWithOwner(BaseModel):
    title: str
    description: str = None
    price: float
    location_link: str = None
    latitude: float = None
    longitude: float = None
    owner_email: str
    owner_password: str

# --- Dashboard Stats Schemas ---

class PlatformStats(BaseModel):
    visits: int = 0
    new_users: int = 0
    new_owners: int = 0
    saves: int = 0
    directions: int = 0
    calls: int = 0
    reviews: int = 0
    chats: int = 0
    resolved_chats: int = 0
    active_places: int = 0
    
    # Deltas (optional, strings like "+5%")
    visits_delta: str = None
    users_delta: str = None
    saves_delta: str = None
    directions_delta: str = None
    calls_delta: str = None
    reviews_delta: str = None

class TrendingDay(BaseModel):
    date: str
    visits: int = 0
    new_users: int = 0
    new_owners: int = 0
    saves: int = 0
    directions: int = 0
    calls: int = 0
    reviews: int = 0
    chats: int = 0

class PlaceStats(BaseModel):
    place_id: str
    name: str
    category: str
    district: str = "Beni Suef"
    visits: int = 0
    saves: int = 0
    rating: float = 0.0
    reviews: int = 0
    status: str
    added: str

class UserStats(BaseModel):
    user_id: str
    name: str
    district: str = "Beni Suef"
    reviews: int = 0
    saves: int = 0
    status: str
    joined: str
    last_login: str = None
