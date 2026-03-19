from typing import Optional

from pydantic import BaseModel, field_validator


class RestaurantProfileUpdate(BaseModel):
    name: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("name cannot be empty")
        return v


class RestaurantProfileOut(BaseModel):
    restaurant_id: str
    name: str
