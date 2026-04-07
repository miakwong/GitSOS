# Feat9 — Business logic for review submission and retrieval
import uuid

from app.repositories import review_repository
from app.repositories.order_repository import OrderRepository
from app.schemas.constants import REVIEW_REQUIRED_ORDER_STATUS
from app.schemas.review import (
    RestaurantRatingSummary,
    ReviewCreate,
    ReviewOut,
    ReviewRecord,
)

ReviewError = ValueError


_order_repo = OrderRepository()


def submit_review(payload: ReviewCreate, customer_id: str) -> ReviewOut:
    order_id = payload.order_id

    # Only system-created orders can be reviewed (not Kaggle historical data)
    order = _order_repo.get_order_by_id(str(order_id))
    if order is None:
        raise ReviewError(
            f"Order '{order_id}' not found or is not a system-created order. "
            "Only orders placed through this platform can be reviewed."
        )

    # Order must belong to the requesting customer
    if order.customer_id != customer_id:
        raise PermissionError("You can only review your own orders.")

    # Order must be in Delivered status
    if order.order_status.value != REVIEW_REQUIRED_ORDER_STATUS:
        raise ReviewError(
            f"Reviews can only be submitted for delivered orders. "
            f"Current status: '{order.order_status.value}'"
        )

    # No duplicate review per order
    existing = review_repository.get_by_order_id(order_id)
    if existing is not None:
        raise ReviewError(f"A review already exists for order '{order_id}'.")

    record = ReviewRecord(
        review_id=uuid.uuid4(),
        order_id=order_id,
        customer_id=uuid.UUID(customer_id),
        restaurant_id=order.restaurant_id,
        rating=payload.rating,
        tags=payload.tags,
    )
    saved = review_repository.create(record)
    return ReviewOut.from_record(saved)


def delete_review(review_id: uuid.UUID, requester_id: str, requester_role: str) -> None:
    record = review_repository.get_by_id(review_id)
    if record is None:
        raise ReviewError(f"Review '{review_id}' not found.")

    # Only the author or an admin may delete
    if requester_role != "admin" and str(record.customer_id) != requester_id:
        raise PermissionError("You can only delete your own reviews.")

    review_repository.delete(review_id)


def get_restaurant_ratings(restaurant_id: int) -> RestaurantRatingSummary:
    records = review_repository.get_by_restaurant_id(restaurant_id)
    reviews = [ReviewOut.from_record(r) for r in records]

    if not reviews:
        return RestaurantRatingSummary(
            restaurant_id=restaurant_id,
            review_count=0,
            average_rating=0.0,
            tag_counts={},
            reviews=[],
        )

    avg = round(sum(r.rating for r in reviews) / len(reviews), 2)

    tag_counts: dict = {}
    for r in reviews:
        for tag in r.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return RestaurantRatingSummary(
        restaurant_id=restaurant_id,
        review_count=len(reviews),
        average_rating=avg,
        tag_counts=tag_counts,
        reviews=reviews,
    )
