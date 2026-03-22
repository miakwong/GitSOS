from pydantic import BaseModel, Field


# Below is the breakdown of the delivery fee components
class DeliveryFeeBreakdown(BaseModel):
    base_fee: float = Field(..., ge=0, description="Fixed base fee ($3.00)")
    distance_fee: float = Field(..., ge=0, description="Progressive fee based on distance")
    method_surcharge: float = Field(..., ge=0, description="Surcharge based on delivery method (Walk/Bike/Car)")
    traffic_surcharge: float = Field(..., ge=0, description="Surcharge based on traffic condition")
    weather_surcharge: float = Field(..., ge=0, description="Surcharge based on weather condition")
    condition_surcharge: float = Field(..., ge=0, description="Total condition surcharge (traffic + weather)")
    total_delivery_fee: float = Field(..., ge=0, description="Total delivery fee")


# Full price breakdown returned to the client
class PriceBreakdownResponse(BaseModel):
    order_id: str = Field(..., description="The order ID")
    food_price: float = Field(..., ge=0, description="Food base price from Kaggle data")
    delivery_fee: DeliveryFeeBreakdown = Field(..., description="Itemized delivery fee breakdown")
    subtotal: float = Field(..., ge=0, description="Food price + total delivery fee")
    tax: float = Field(..., ge=0, description="Tax applied to subtotal (5%)")
    total: float = Field(..., ge=0, description="Final total (subtotal + tax)")
