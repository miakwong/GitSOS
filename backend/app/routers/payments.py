# routers/payments.py
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas.payment import PaymentOut
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment_status(payment_id: UUID) -> PaymentOut:
    result = payment_service.get_payment_status(payment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return result


@router.get("/order/{order_id}", response_model=PaymentOut)
def get_payment_by_order(order_id: UUID) -> PaymentOut:
    result = payment_service.get_payment_by_order(order_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Payment not found for order")
    return result
