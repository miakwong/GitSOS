import uuid
from uuid import UUID

from app.repositories import favourite_repository
from app.repositories.order_repository import OrderRepository
from app.schemas.favourite import FavouriteCreate, FavouriteOut, FavouriteRecord
from app.schemas.order import Order, OrderCreate
from app.services.order_service import OrderService
from fastapi import HTTPException, status


_order_repo = OrderRepository()
_order_service = OrderService()


def add_favourite(payload: FavouriteCreate, customer_id: str) -> FavouriteOut:
    order = _order_repo.get_order_by_id(str(payload.order_id))
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{payload.order_id}' not found.",
        )

    cust_uuid = UUID(customer_id)

    if favourite_repository.exists(cust_uuid, payload.order_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order '{payload.order_id}' is already in your favourites.",
        )

    record = FavouriteRecord(
        favourite_id=uuid.uuid4(),
        order_id=payload.order_id,
        customer_id=cust_uuid,
    )
    saved = favourite_repository.create(record)
    return FavouriteOut.from_record(saved)


def get_favourites(customer_id: str) -> list[FavouriteOut]:
    records = favourite_repository.get_by_customer(UUID(customer_id))
    return [FavouriteOut.from_record(r) for r in records]


def remove_favourite(favourite_id: UUID, customer_id: str) -> None:
    record = favourite_repository.get_by_id(favourite_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Favourite '{favourite_id}' not found.",
        )

    if str(record.customer_id) != customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only remove your own favourites.",
        )

    favourite_repository.delete(favourite_id)


def reorder_from_favourite(favourite_id: UUID, customer_id: str) -> Order:
    # look up the favourite
    record = favourite_repository.get_by_id(favourite_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Favourite '{favourite_id}' not found.",
        )

    # make sure the favourite belongs to the requesting customer
    if str(record.customer_id) != customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reorder from your own favourites.",
        )

    # fetch the original order that was saved as favourite
    original_order = _order_repo.get_order_by_id(str(record.order_id))
    if original_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The original order linked to this favourite no longer exists.",
        )

    # build a new order using the same details as the original
    order_data = OrderCreate(
        customer_id=customer_id,
        restaurant_id=original_order.restaurant_id,
        food_item=original_order.food_item,
        order_value=original_order.order_value,
        delivery_distance=original_order.delivery_distance,
        delivery_method=original_order.delivery_method,
        traffic_condition=original_order.traffic_condition,
        weather_condition=original_order.weather_condition,
    )

    # create the new order through the normal order service (runs all validations)
    new_order = _order_service.create_order(order_data)
    return new_order
