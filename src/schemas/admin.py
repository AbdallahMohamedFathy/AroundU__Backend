from pydantic import BaseModel

class UserPromotion(BaseModel):
    role: str # ADMIN, OWNER, USER
