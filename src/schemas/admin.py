from pydantic import BaseModel

class UserPromotion(BaseModel):
    role: str # ADMIN, OWNER, USER

class PlaceCreateWithOwner(BaseModel):
    place_name: str
    description: str = None
    category_id: int
    latitude: float
    longitude: float
    owner_email: str
    owner_password: str

class PlaceCreationResponse(BaseModel):
    place_id: int
    owner_id: int
    owner_email: str
