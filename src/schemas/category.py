from pydantic import BaseModel
from typing import Optional

class CategoryBase(BaseModel):
    name: str
    icon: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int

    class Config:
        orm_mode = True

