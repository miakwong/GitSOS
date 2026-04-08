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
from app.schemas.constants import PAYMENT_STATUS_SUCCESS, PAYMENT_STATUS_FAILED, PAYMENT_STATUS_REFUNDED


order_repo = OrderRepository()


<<<<<<< HEAD
def get_order_summary() -> OrderSummaryReport:
    all_orders = order_repo.get_all_orders()
    
    total_orders = len(all_orders)
    completed_orders = sum(1 for o in all_orders if o.order_status == OrderStatus.DELIVERED)
    cancelled_orders = sum(1 for o in all_orders if o.order_status == OrderStatus.CANCELLED)
    pending_orders = sum(1 for o in all_orders if o.order_status in [OrderStatus.PLACED, OrderStatus.PAID, OrderStatus.PREPARING])
    total_revenue = sum(o.order_value for o in all_orders if o.order_status == OrderStatus.DELIVERED)
    
=======
def get_order_summary(date_start=None, date_end=None, restaurant_id=None) -> OrderSummaryReport:
    all_orders = order_repo.get_all_orders()
    filtered_orders = []
    for o in all_orders:
        if restaurant_id and hasattr(o, 'restaurant_id') and o.restaurant_id != restaurant_id:
            continue
        if date_start and hasattr(o, 'created_at'):
            created = o.created_at if isinstance(o.created_at, datetime) else datetime.fromisoformat(o.created_at)
            if created.date() < date_start:
                continue
        if date_end and hasattr(o, 'created_at'):
            created = o.created_at if isinstance(o.created_at, datetime) else datetime.fromisoformat(o.created_at)
            if created.date() > date_end:
                continue
        filtered_orders.append(o)
    total_orders = len(filtered_orders)
    completed_orders = sum(1 for o in filtered_orders if o.order_status == OrderStatus.DELIVERED)
    cancelled_orders = sum(1 for o in filtered_orders if o.order_status == OrderStatus.CANCELLED)
    pending_orders = sum(1 for o in filtered_orders if o.order_status in [OrderStatus.PLACED, OrderStatus.PAID, OrderStatus.PREPARING])
    total_revenue = sum(o.order_value for o in filtered_orders if o.order_status == OrderStatus.DELIVERED)
>>>>>>> feat/10-B2-scoped-reports
    return OrderSummaryReport(
        total_orders=total_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        pending_orders=pending_orders,
        total_revenue=total_revenue,
    )


<<<<<<< HEAD
def get_delivery_summary() -> DeliverySummaryReport:
    all_orders = order_repo.get_all_orders()
    
    completed_deliveries = sum(1 for o in all_orders if o.order_status == OrderStatus.DELIVERED)
    pending_deliveries = sum(1 for o in all_orders if o.order_status in [OrderStatus.PLACED, OrderStatus.PAID, OrderStatus.PREPARING])
    total_deliveries = completed_deliveries + pending_deliveries
    
    average_delivery_time = None
    if completed_deliveries > 0:
        total_time = 0
        for o in all_orders:
=======
def get_delivery_summary(date_start=None, date_end=None, restaurant_id=None) -> DeliverySummaryReport:
    all_orders = order_repo.get_all_orders()
    filtered_orders = []
    for o in all_orders:
        if restaurant_id and hasattr(o, 'restaurant_id') and o.restaurant_id != restaurant_id:
            continue
        if date_start and hasattr(o, 'created_at'):
            created = o.created_at if isinstance(o.created_at, datetime) else datetime.fromisoformat(o.created_at)
            if created.date() < date_start:
                continue
        if date_end and hasattr(o, 'created_at'):
            created = o.created_at if isinstance(o.created_at, datetime) else datetime.fromisoformat(o.created_at)
            if created.date() > date_end:
                continue
        filtered_orders.append(o)
    completed_deliveries = sum(1 for o in filtered_orders if o.order_status == OrderStatus.DELIVERED)
    pending_deliveries = sum(1 for o in filtered_orders if o.order_status in [OrderStatus.PLACED, OrderStatus.PAID, OrderStatus.PREPARING])
    total_deliveries = completed_deliveries + pending_deliveries
    average_delivery_time = None
    if completed_deliveries > 0:
        total_time = 0
        for o in filtered_orders:
>>>>>>> feat/10-B2-scoped-reports
            if o.order_status == OrderStatus.DELIVERED:
                if hasattr(o, 'created_at') and hasattr(o, 'delivery_time') and o.delivery_time:
                    try:
                        created = o.created_at if isinstance(o.created_at, datetime) else datetime.fromisoformat(o.created_at)
                        delivered = o.delivery_time if isinstance(o.delivery_time, datetime) else datetime.fromisoformat(o.delivery_time)
                        total_time += (delivered - created).total_seconds() / 60
                    except:
                        pass
        average_delivery_time = total_time / completed_deliveries if completed_deliveries > 0 else None
<<<<<<< HEAD
    
=======
>>>>>>> feat/10-B2-scoped-reports
    return DeliverySummaryReport(
        total_deliveries=total_deliveries,
        completed_deliveries=completed_deliveries,
        pending_deliveries=pending_deliveries,
        average_delivery_time=average_delivery_time,
    )


<<<<<<< HEAD
def get_payment_summary() -> PaymentSummaryReport:
    all_payments = payment_repository.list_all()
    
    total_transactions = len(all_payments)
    successful_payments = sum(1 for p in all_payments if p.status == PAYMENT_STATUS_SUCCESS)
    failed_payments = sum(1 for p in all_payments if p.status == PAYMENT_STATUS_FAILED)
    total_revenue = sum(p.amount for p in all_payments if p.status == PAYMENT_STATUS_SUCCESS)
    total_refunds = sum(p.amount for p in all_payments if p.status == PAYMENT_STATUS_REFUNDED)
    
=======
def get_payment_summary(date_start=None, date_end=None, restaurant_id=None) -> PaymentSummaryReport:
    all_payments = payment_repository.list_all()
    filtered_payments = []
    for p in all_payments:
        if restaurant_id and hasattr(p, 'restaurant_id') and p.restaurant_id != restaurant_id:
            continue
        if date_start and hasattr(p, 'created_at'):
            created = p.created_at if isinstance(p.created_at, datetime) else datetime.fromisoformat(p.created_at)
            if created.date() < date_start:
                continue
        if date_end and hasattr(p, 'created_at'):
            created = p.created_at if isinstance(p.created_at, datetime) else datetime.fromisoformat(p.created_at)
            if created.date() > date_end:
                continue
        filtered_payments.append(p)
    total_transactions = len(filtered_payments)
    successful_payments = sum(1 for p in filtered_payments if p.status == PAYMENT_STATUS_SUCCESS)
    failed_payments = sum(1 for p in filtered_payments if p.status == PAYMENT_STATUS_FAILED)
    total_revenue = sum(p.amount for p in filtered_payments if p.status == PAYMENT_STATUS_SUCCESS)
    total_refunds = sum(p.amount for p in filtered_payments if p.status == PAYMENT_STATUS_REFUNDED)
>>>>>>> feat/10-B2-scoped-reports
    return PaymentSummaryReport(
        total_transactions=total_transactions,
        total_revenue=total_revenue,
        successful_payments=successful_payments,
        failed_payments=failed_payments,
        total_refunds=total_refunds,
    )


<<<<<<< HEAD
def get_review_summary() -> ReviewSummaryReport:
    all_reviews = review_repository.list_all()
    
    total_reviews = len(all_reviews)
    average_rating = sum(r.rating for r in all_reviews) / total_reviews if total_reviews > 0 else 0.0
    five_star_reviews = sum(1 for r in all_reviews if r.rating == 5)
    one_star_reviews = sum(1 for r in all_reviews if r.rating == 1)
    total_restaurants_reviewed = len(set(r.restaurant_id for r in all_reviews if r.restaurant_id))
    
=======
def get_review_summary(date_start=None, date_end=None, restaurant_id=None) -> ReviewSummaryReport:
    all_reviews = review_repository.list_all()
    filtered_reviews = []
    for r in all_reviews:
        if restaurant_id and hasattr(r, 'restaurant_id') and r.restaurant_id != restaurant_id:
            continue
        if date_start and hasattr(r, 'created_at'):
            created = r.created_at if isinstance(r.created_at, datetime) else datetime.fromisoformat(r.created_at)
            if created.date() < date_start:
                continue
        if date_end and hasattr(r, 'created_at'):
            created = r.created_at if isinstance(r.created_at, datetime) else datetime.fromisoformat(r.created_at)
            if created.date() > date_end:
                continue
        filtered_reviews.append(r)
    total_reviews = len(filtered_reviews)
    average_rating = sum(r.rating for r in filtered_reviews) / total_reviews if total_reviews > 0 else 0.0
    five_star_reviews = sum(1 for r in filtered_reviews if r.rating == 5)
    one_star_reviews = sum(1 for r in filtered_reviews if r.rating == 1)
    total_restaurants_reviewed = len(set(r.restaurant_id for r in filtered_reviews if r.restaurant_id))
>>>>>>> feat/10-B2-scoped-reports
    return ReviewSummaryReport(
        total_reviews=total_reviews,
        average_rating=round(average_rating, 2),
        total_restaurants_reviewed=total_restaurants_reviewed,
        five_star_reviews=five_star_reviews,
        one_star_reviews=one_star_reviews,
    )


def get_system_summary(date_start=None, date_end=None, restaurant_id=None) -> SystemSummaryReport:
    return SystemSummaryReport(
        orders=get_order_summary(date_start, date_end, restaurant_id),
        deliveries=get_delivery_summary(date_start, date_end, restaurant_id),
        payments=get_payment_summary(date_start, date_end, restaurant_id),
        reviews=get_review_summary(date_start, date_end, restaurant_id),

    )
