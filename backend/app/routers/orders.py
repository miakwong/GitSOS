# Orders router for API endpoints
from fastapi import APIRouter, status

from app.schemas.order import Order, OrderCreate, OrderUpdate
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])

# Service instance
order_service = OrderService()


# Create a new system order
@router.post(
    "/",
    response_model=Order,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new system order",
    description="Creates a new order with validated customer, restaurant, and food item associations.",
)
def create_order(order_data: OrderCreate) -> Order:
    return order_service.create_order(order_data)


# Retrieve all system-created orders
@router.get(
    "/",
    response_model=list[Order],
    summary="Get all system orders",
    description="Retrieves all system-created orders.",
)
def get_all_orders() -> list[Order]:
    return order_service.get_all_orders()


# Retrieve a system order by ID
@router.get(
    "/{order_id}",
    response_model=Order,
    summary="Get a system order by ID",
    description="Retrieves a specific system-created order by its UUID.",
)
def get_order(order_id: str) -> Order:
    return order_service.get_order(order_id)


# Update a system order (customer can only update their own orders in "Placed" status)
@router.put(
    "/{order_id}",
    response_model=Order,
    summary="Update a system order",
    description="Updates a system order. Only the order owner can update, and only if order is in 'Placed' status.",
)
def update_order(order_id: str, customer_id: str, update_data: OrderUpdate) -> Order:
    return order_service.update_order(order_id, customer_id, update_data)


# Cancel a system order (customer can only cancel their own orders in "Placed" status)
@router.delete(
    "/{order_id}/cancel",
    response_model=Order,
    summary="Cancel a system order",
    description="Cancels a system order. Only the order owner can cancel, and only if order is in 'Placed' status.",
)
def cancel_order(order_id: str, customer_id: str) -> Order:
    return order_service.cancel_order(order_id, customer_id)
