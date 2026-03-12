# routers/payments.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user_full
from app.schemas.payment import PaymentCreate, PaymentOut
from app.schemas.user import UserInDB
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


def _check_payment_access(payment: PaymentOut, current_user: UserInDB) -> None:
    """
    Enforce role-based access:
    - admin: can view all payments
    - customer: can only view their own payments
    - owner: [FEAT4] restrict to orders linked to their restaurant
              for now treated same as customer (by customer_id)
    """
    if current_user.role == "admin":
        return
    if str(current_user.id) != payment.customer_id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.post("/", response_model=PaymentOut, status_code=201)
def process_payment(
    payload: PaymentCreate,
    current_user: UserInDB = Depends(get_current_user_full),
) -> PaymentOut:
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
