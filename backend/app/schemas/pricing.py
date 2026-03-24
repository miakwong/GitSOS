from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DeliveryFeeBreakdown(BaseModel):
    base_fee: float = Field(..., ge=0)
    distance_fee: float = Field(..., ge=0)
    method_fee: float = Field(..., ge=0)
    condition_fee: float = Field(..., ge=0)
    total_delivery_fee: float = Field(..., ge=0)


class PriceBreakdownResponse(BaseModel):
    order_id: str
    food_price: float = Field(..., ge=0)
    delivery_fee: DeliveryFeeBreakdown
    subtotal: float = Field(..., ge=0)
    tax: float = Field(..., ge=0)
    total: float = Field(..., ge=0)


class PricingAnalyticsResponse(BaseModel):
    total_orders: int
    total_revenue: float = Field(..., ge=0)
    avg_order_value: Optional[float] = None   # None when there are no orders
    min_order_value: Optional[float] = None   # As above
    max_order_value: Optional[float] = None   # As above