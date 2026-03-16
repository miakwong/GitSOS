from typing import Optional

from pydantic import BaseModel, field_validator


class MenuItemCreate(BaseModel):
    food_item: str
    price: float

    @field_validator("food_item")
    @classmethod
    def food_item_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("food_item cannot be empty")
        return v.strip()

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("price must be greater than 0")
        return v


class MenuItemUpdate(BaseModel):
    food_item: Optional[str] = None
    price: Optional[float] = None

    @field_validator("food_item")
    @classmethod
    def food_item_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("food_item cannot be empty")
        return v.strip() if v else v

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("price must be greater than 0")
        return v


class MenuItemOut(BaseModel):
    restaurant_id: str
    food_item: str
    price: float
