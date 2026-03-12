from pydantic import BaseModel


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
    name: str  # "Restaurant_{restaurant_id}"


class KaggleMenuItem(BaseModel):
    restaurant_id: str
    food_item: str
    median_price: float  # precomputed from all order_value entries for this food_item
