# routers/payments.py
from uuid import UUID

from app.dependencies import get_current_user_full
from app.schemas.constants import ROLE_ADMIN, ROLE_OWNER
from app.schemas.payment import PaymentCreate, PaymentOut
from app.schemas.user import UserInDB
from app.services import payment_service
from app.services.order_service import OrderService
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/payments", tags=["payments"])

_order_service = OrderService()


def _check_payment_access(payment: PaymentOut, current_user: UserInDB) -> None:
    """
    Enforce role-based access:
    - admin: can view all payments
    - owner: can view payments for orders belonging to their restaurant
    - customer: can only view their own payments
    """
    if current_user.role == ROLE_ADMIN:
        return
    if current_user.role == ROLE_OWNER:
        order = _order_service.get_order(payment.order_id)
        if order.restaurant_id == current_user.restaurant_id:
            return
        raise HTTPException(status_code=403, detail="Access denied")
    if str(current_user.id) != payment.customer_id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.post("/", response_model=PaymentOut, status_code=201)
def process_payment(
    payload: PaymentCreate,
    current_user: UserInDB = Depends(get_current_user_full),
) -> PaymentOut:
    if current_user.role != ROLE_ADMIN:
        order = _order_service.get_order(str(payload.order_id))
        if order.customer_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
    try:
        return payment_service.process_payment(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment_status(
    payment_id: UUID,
    current_user: UserInDB = Depends(get_current_user_full),
) -> PaymentOut:
    result = payment_service.get_payment_status(payment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    _check_payment_access(result, current_user)
    return result


@router.get("/order/{order_id}", response_model=PaymentOut)
def get_payment_by_order(
    order_id: UUID,
    current_user: UserInDB = Depends(get_current_user_full),
) -> PaymentOut:
    result = payment_service.get_payment_by_order(order_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Payment not found for order")
    _check_payment_access(result, current_user)
    return result
