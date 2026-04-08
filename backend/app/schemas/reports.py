from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class OrderSummaryReport(BaseModel):
    total_orders: int
    total_amount: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    restaurant_id: Optional[str] = None

class DeliverySummaryReport(BaseModel):
    total_deliveries: int
    average_delivery_time: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    restaurant_id: Optional[str] = None

class PaymentSummaryReport(BaseModel):
    total_payments: int
    total_revenue: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    restaurant_id: Optional[str] = None

class ReviewSummaryReport(BaseModel):
    total_reviews: int
    average_rating: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    restaurant_id: Optional[str] = None

class SystemSummaryReport(BaseModel):
    order_summary: OrderSummaryReport
    delivery_summary: DeliverySummaryReport
    payment_summary: PaymentSummaryReport
    review_summary: ReviewSummaryReport
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    restaurant_id: Optional[str] = None
