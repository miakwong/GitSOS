# schemas for delivery info and delivery outcome recording
from typing import Optional

from pydantic import BaseModel, Field


# used to record delivery outcome after order reaches Delivered status
class DeliveryOutcomeCreate(BaseModel):
    actual_delivery_time: float = Field(..., gt=0, description="Actual delivery time in minutes")
    delivery_delay: float = Field(..., description="Delay vs expected time in minutes (0 = on time)")


# delivery info for both system orders and Kaggle historical orders
class DeliveryInfo(BaseModel):
    order_id: str
    delivery_distance: float

    # only present for system-created orders
    delivery_method: Optional[str] = None
    traffic_condition: Optional[str] = None
    weather_condition: Optional[str] = None

    # only present for Kaggle historical orders
    delivery_time: Optional[float] = None   # actual delivery time in minutes
    delivery_delay: Optional[float] = None  # delay vs expected, in minutes

    # True if this came from the Kaggle dataset, False if it's a system-created order
    is_historical: bool = False
