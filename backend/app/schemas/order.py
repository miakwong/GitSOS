# Order schemas for system-created orders
from enum import Enum
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# order status values for system-created orders
class OrderStatus(str, Enum):
    PLACED = "Placed"
    PAID = "Paid"
    PREPARING = "Preparing"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


#  delivery method values
class DeliveryMethod(str, Enum):
    WALK = "Walk"
    BIKE = "Bike"
    CAR = "Car"


#  traffic condition values
class TrafficCondition(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


#  weather condition values
class WeatherCondition(str, Enum):
    SUNNY = "Sunny"
    RAINY = "Rainy"
    SNOWY = "Snowy"


# creating a system order
class OrderCreate(BaseModel):
    customer_id: str = Field(..., description="ID of the customer placing the order")
    restaurant_id: int = Field(..., description="ID of the restaurant")
    food_item: str = Field(..., min_length=1, description="Non-empty food item name")
    order_value: float = Field(..., gt=0, description="Order value in dollars")
    delivery_distance: float = Field(
        ..., ge=2.0, le=15.0,
        description="Delivery distance in km (2.0–15.0 inclusive)"
    )
    delivery_method: DeliveryMethod = Field(..., description="Delivery method")
    traffic_condition: Optional[TrafficCondition] = Field(
        default=TrafficCondition.LOW,
        description="Traffic condition (defaults to Low)"
    )
    weather_condition: Optional[WeatherCondition] = Field(
        default=WeatherCondition.SUNNY,
        description="Weather condition (defaults to Sunny)"
    )

    @field_validator("food_item")
    @classmethod
    # make sure food_item is not empty 
    def validate_food_item_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("food_item must not be empty or whitespace")
        return v.strip()



class Order(BaseModel):
    order_id: UUID = Field(..., description="Unique UUID for the order")
    customer_id: str = Field(..., description="ID of the customer")
    restaurant_id: int = Field(..., description="ID of the restaurant")
    food_item: str = Field(..., description="Food item ordered")
    order_time: datetime = Field(..., description="Timestamp when order was placed")
    order_value: float = Field(..., description="Order value in dollars")
    delivery_distance: float = Field(..., description="Delivery distance in km")
    delivery_method: DeliveryMethod = Field(..., description="Delivery method")
    traffic_condition: TrafficCondition = Field(..., description="Traffic condition")
    weather_condition: WeatherCondition = Field(..., description="Weather condition")
    order_status: OrderStatus = Field(..., description="Current order status")

    model_config = {"from_attributes": True}


# updating a system order
class OrderUpdate(BaseModel):
    food_item: Optional[str] = Field(None, min_length=1, description="New food item name")
    order_value: Optional[float] = Field(None, gt=0, description="New order value in dollars")
    delivery_distance: Optional[float] = Field(
        None, ge=2.0, le=15.0,
        description="New delivery distance in km (2.0–15.0 inclusive)"
    )
    delivery_method: Optional[DeliveryMethod] = Field(None, description="New delivery method")
    traffic_condition: Optional[TrafficCondition] = Field(None, description="New traffic condition")
    weather_condition: Optional[WeatherCondition] = Field(None, description="New weather condition")

    @field_validator("food_item")
    @classmethod
    def validate_food_item_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("food_item must not be empty or whitespace")
        return v.strip() if v else v


# Order statuses that allow modification
MODIFIABLE_STATUSES = {OrderStatus.PLACED}

# Order statuses that allow cancellation
CANCELLABLE_STATUSES = {OrderStatus.PLACED, OrderStatus.PAID}

#  workflow transitions for system-created orders

VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PLACED: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


# owner/admin status update endpoints
class OrderStatusUpdate(BaseModel):
    order_status: OrderStatus = Field(..., description="The new status to transition the order to")
