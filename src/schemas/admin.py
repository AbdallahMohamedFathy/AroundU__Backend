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
