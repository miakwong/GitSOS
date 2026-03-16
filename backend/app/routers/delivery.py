# Delivery router - read-only endpoints for viewing delivery info linked to an order
from app.dependencies import get_current_user
from app.schemas.delivery import DeliveryInfo
from app.schemas.user import UserInDB
from app.services.delivery_service import DeliveryService
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/delivery", tags=["delivery"])

# shared service instance (can be overridden in tests via monkeypatch)
delivery_service = DeliveryService()


# Get delivery info for a specific order (read-only)
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
