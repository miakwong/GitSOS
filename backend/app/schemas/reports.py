from pydantic import BaseModel
from typing import Optional


class OrderSummaryReport(BaseModel):
    total_orders: int
    completed_orders: int
    cancelled_orders: int
    pending_orders: int
    total_revenue: float


class DeliverySummaryReport(BaseModel):
    total_deliveries: int
    completed_deliveries: int
    pending_deliveries: int
    average_delivery_time: Optional[float]


class PaymentSummaryReport(BaseModel):
    total_transactions: int
    total_revenue: float
    successful_payments: int
    failed_payments: int
    total_refunds: float


class ReviewSummaryReport(BaseModel):
    total_reviews: int
    average_rating: float
    total_restaurants_reviewed: int
    five_star_reviews: int
    one_star_reviews: int


class SystemSummaryReport(BaseModel):
    orders: OrderSummaryReport
    deliveries: DeliverySummaryReport
    payments: PaymentSummaryReport
    reviews: ReviewSummaryReport
