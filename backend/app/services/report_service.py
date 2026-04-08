from datetime import datetime
from app.repositories.order_repository import OrderRepository
from app.repositories import payment_repository
from app.repositories import review_repository
from app.schemas.reports import (
    OrderSummaryReport,
    DeliverySummaryReport,
    PaymentSummaryReport,
    ReviewSummaryReport,
    SystemSummaryReport,
)
from app.schemas.order import OrderStatus
from app.schemas.constants import PAYMENT_STATUS_SUCCESS, PAYMENT_STATUS_FAILED


order_repo = OrderRepository()


def get_order_summary() -> OrderSummaryReport:
    all_orders = order_repo.get_all_orders()
    
    total_orders = len(all_orders)
    completed_orders = sum(1 for o in all_orders if o.get("order_status") == OrderStatus.DELIVERED)
    cancelled_orders = sum(1 for o in all_orders if o.get("order_status") == OrderStatus.CANCELLED)
    pending_orders = sum(1 for o in all_orders if o.get("order_status") in [OrderStatus.PLACED, OrderStatus.PAID, OrderStatus.PREPARING])
    total_revenue = sum(o.get("total_price", 0) for o in all_orders if o.get("order_status") == OrderStatus.DELIVERED)
    
    return OrderSummaryReport(
        total_orders=total_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        pending_orders=pending_orders,
        total_revenue=total_revenue,
    )


def get_delivery_summary() -> DeliverySummaryReport:
    all_orders = order_repo.get_all_orders()
    
    completed_deliveries = sum(1 for o in all_orders if o.get("order_status") == OrderStatus.DELIVERED)
    pending_deliveries = sum(1 for o in all_orders if o.get("order_status") in [OrderStatus.PLACED, OrderStatus.PAID, OrderStatus.PREPARING])
    total_deliveries = completed_deliveries + pending_deliveries
    
    average_delivery_time = None
    if completed_deliveries > 0:
        total_time = 0
        for o in all_orders:
            if o.get("order_status") == OrderStatus.DELIVERED:
                if "created_at" in o and "delivery_time" in o:
                    try:
                        created = datetime.fromisoformat(o["created_at"])
                        delivered = datetime.fromisoformat(o["delivery_time"])
                        total_time += (delivered - created).total_seconds() / 60
                    except:
                        pass
        average_delivery_time = total_time / completed_deliveries if completed_deliveries > 0 else None
    
    return DeliverySummaryReport(
        total_deliveries=total_deliveries,
        completed_deliveries=completed_deliveries,
        pending_deliveries=pending_deliveries,
        average_delivery_time=average_delivery_time,
    )


def get_payment_summary() -> PaymentSummaryReport:
    all_payments = payment_repository.list_all()
    
    total_transactions = len(all_payments)
    successful_payments = sum(1 for p in all_payments if p.status == PAYMENT_STATUS_SUCCESS)
    failed_payments = sum(1 for p in all_payments if p.status == PAYMENT_STATUS_FAILED)
    total_revenue = sum(p.amount for p in all_payments if p.status == PAYMENT_STATUS_SUCCESS)
    total_refunds = 0
    
    return PaymentSummaryReport(
        total_transactions=total_transactions,
        total_revenue=total_revenue,
        successful_payments=successful_payments,
        failed_payments=failed_payments,
        total_refunds=total_refunds,
    )


def get_review_summary() -> ReviewSummaryReport:
    all_reviews = review_repository.list_all()
    
    total_reviews = len(all_reviews)
    average_rating = sum(r.rating for r in all_reviews) / total_reviews if total_reviews > 0 else 0.0
    five_star_reviews = sum(1 for r in all_reviews if r.rating == 5)
    one_star_reviews = sum(1 for r in all_reviews if r.rating == 1)
    total_restaurants_reviewed = len(set(r.restaurant_id for r in all_reviews if r.restaurant_id))
    
    return ReviewSummaryReport(
        total_reviews=total_reviews,
        average_rating=round(average_rating, 2),
        total_restaurants_reviewed=total_restaurants_reviewed,
        five_star_reviews=five_star_reviews,
        one_star_reviews=one_star_reviews,
    )


def get_system_summary() -> SystemSummaryReport:
    return SystemSummaryReport(
        orders=get_order_summary(),
        deliveries=get_delivery_summary(),
        payments=get_payment_summary(),
        reviews=get_review_summary(),
    )
