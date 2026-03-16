# Schema for delivery info returned by the delivery endpoint
from typing import Optional

from pydantic import BaseModel


# Unified delivery info for both system orders and Kaggle historical orders
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

    # True if this came from the Kaggle dataset (read-only historical record)
    is_historical: bool = False
