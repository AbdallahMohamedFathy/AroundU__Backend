from pydantic import BaseModel, ConfigDict
from typing import Optional

class CategoryBase(BaseModel):
    name: str
    icon: Optional[str] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    icon: str | None

    model_config = ConfigDict(from_attributes=True)

