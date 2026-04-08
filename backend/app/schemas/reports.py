from pydantic import BaseModel
<<<<<<< HEAD
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

=======
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
>>>>>>> feat/10-B2-scoped-reports

class ReviewSummaryReport(BaseModel):
    total_reviews: int
    average_rating: float
<<<<<<< HEAD
    total_restaurants_reviewed: int
    five_star_reviews: int
    one_star_reviews: int


from pydantic import BaseModel
from typing import Optional
from datetime import date

class OrderSummaryReport(BaseModel):
    total_orders: int
    completed_orders: int
    cancelled_orders: int
    pending_orders: int
    total_revenue: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    restaurant_id: Optional[str] = None

class DeliverySummaryReport(BaseModel):
    total_deliveries: int
    completed_deliveries: int
    pending_deliveries: int
    average_delivery_time: Optional[float]
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    restaurant_id: Optional[str] = None

class PaymentSummaryReport(BaseModel):
    total_transactions: int
    total_revenue: float
    successful_payments: int
    failed_payments: int
    total_refunds: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    restaurant_id: Optional[str] = None

class ReviewSummaryReport(BaseModel):
    total_reviews: int
    average_rating: float
    total_restaurants_reviewed: int
    five_star_reviews: int
    one_star_reviews: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    restaurant_id: Optional[str] = None

class SystemSummaryReport(BaseModel):
    orders: OrderSummaryReport
    deliveries: DeliverySummaryReport
    payments: PaymentSummaryReport
    reviews: ReviewSummaryReport
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    restaurant_id: Optional[str] = None
