# Delivery router - endpoints for viewing delivery info and recording delivery outcomes
from typing import Optional

from app.dependencies import get_current_user
from app.schemas.delivery import DeliveryAnalytics, DeliveryInfo, DeliveryOutcomeCreate
from app.schemas.order import Order
from app.schemas.user import UserInDB
from app.services.delivery_service import DeliveryService
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/delivery", tags=["delivery"])


delivery_service = DeliveryService()


# List delivery records scoped to the current user's role
@router.get(
    "",
    response_model=list[DeliveryInfo],
    summary="List delivery records for the current user",
    description=(
        "Returns delivery records scoped to the authenticated user. "
        "Customers see only their own orders. "
        "Owners see orders for their restaurant (system and Kaggle). "
        "Admins see all records."
    ),
)
def list_delivery_records(
    current_user: UserInDB = Depends(get_current_user),
) -> list[DeliveryInfo]:
    return delivery_service.list_delivery_records(current_user)


# Get delivery analytics filtered by traffic/weather condition (admin only)
@router.get(
    "/analytics",
    response_model=DeliveryAnalytics,
    summary="Get delivery analytics filtered by condition",
    description=(
        "Returns delivery analytics for system orders, optionally filtered by "
        "traffic_condition and/or weather_condition. Admin only."
    ),
)
def get_delivery_analytics(
    traffic_condition: Optional[str] = Query(None, description="Filter by traffic condition"),
    weather_condition: Optional[str] = Query(None, description="Filter by weather condition"),
    current_user: UserInDB = Depends(get_current_user),
) -> DeliveryAnalytics:
    return delivery_service.get_delivery_analytics(
        current_user,
        traffic_condition=traffic_condition,
        weather_condition=weather_condition,
    )


# Get delivery info for a specific order. Customers can only view their own orders, owners can only view orders belonging to their restaurant, and Kaggle historical delivery records are exposed in read-only mode.
@router.get(
    "/{order_id}",
    response_model=DeliveryInfo,
    summary="Get delivery info for an order",
    description=(
        "Returns delivery details linked to the given order_id. "
        "Customers can only view their own orders. "
        "Owners can only view orders belonging to their restaurant. "
        "Kaggle historical delivery records are exposed in read-only mode."
    ),
)
def get_delivery_info(
    order_id: str,
    current_user: UserInDB = Depends(get_current_user),
) -> DeliveryInfo:
    return delivery_service.get_delivery_info(order_id, current_user)


# Record delivery outcome after order reaches Delivered status (owner or admin only)
@router.patch(
    "/{order_id}/outcome",
    response_model=Order,
    summary="Record delivery outcome for a delivered order",
    description=(
        "Records actual_delivery_time and delivery_delay for a system order. "
        "Only allowed after the order status is Delivered. "
        "Outcome fields are immutable once set. "
        "Kaggle historical orders cannot have outcomes recorded."
    ),
)
def record_delivery_outcome(
    order_id: str,
    outcome: DeliveryOutcomeCreate,
    current_user: UserInDB = Depends(get_current_user),
) -> Order:
    return delivery_service.record_delivery_outcome(order_id, outcome, current_user)
