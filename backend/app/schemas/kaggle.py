from pydantic import BaseModel, field_validator


class KaggleOrder(BaseModel):
    order_id: str
    restaurant_id: str
    customer_id: str
    food_item: str
    order_value: float
    order_time: str
    delivery_distance: float
    delivery_time_actual: float
    delivery_delay: float


class KaggleRestaurant(BaseModel):
    restaurant_id: str
    name: str  # restaurant_id  

    @field_validator("restaurant_id")
    @classmethod
    def restaurant_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("restaurant_id cannot be empty")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v


class KaggleMenuItem(BaseModel):
    restaurant_id: str
    food_item: str
    median_price: float  

    @field_validator("restaurant_id")
    @classmethod
    def restaurant_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("restaurant_id cannot be empty")
        return v

    @field_validator("food_item")
    @classmethod
    def food_item_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("food_item cannot be empty")
        return v

    @field_validator("median_price")
    @classmethod
    def median_price_non_negative(cls, v):
        if v < 0:
            raise ValueError("median_price cannot be negative")
        return v
