
# TODO (Feat4 integration): Replace all stubs marked with [FEAT4] once
# Public API:
#   process_payment(payload: PaymentCreate) → PaymentOut
#   get_payment_status(payment_id: UUID)    → Optional[PaymentOut]
#   get_payment_by_order(order_id: UUID)    → Optional[PaymentOut]

import uuid
from typing import Optional

from app.repositories import payment_repository
from app.schemas.constants import PAYMENT_STATUS_SUCCESS
from app.schemas.payment import PaymentCreate, PaymentOut, PaymentRecord


class PaymentError(Exception):
    """Raised when a payment cannot be processed."""


def process_payment(payload: PaymentCreate) -> PaymentOut:
    """
    Simulate a payment for a confirmed order.

    Raises:
        PaymentError: if a payment already exists for this order.

    Returns:
        PaymentOut: the created payment record.
    """
    order_id = payload.order_id

    # Guard: prevent duplicate payments for the same order
    existing = payment_repository.get_by_order_id(order_id)
    if existing is not None:
        raise PaymentError(f"Payment already exists for order {order_id}")

    # Stub: order amount — replace with order_service.get_order(order_id).total
    # when Feat4 order layer is merged
    amount = _get_order_amount(order_id)

    # [FEAT4] Replace with real customer_id from order
    # e.g.: customer_id = order.customer_id
    customer_id = _get_customer_id(order_id)

    record = PaymentRecord(
        payment_id=uuid.uuid4(),
        order_id=order_id,
        customer_id=customer_id,
        status=PAYMENT_STATUS_SUCCESS,
        amount=amount,
    )

    saved = payment_repository.create(record)

    # [FEAT4] After successful payment, update order status to "Paid"
    # e.g.: order_service.update_status(order_id, "Paid")

    return PaymentOut.from_record(saved)


def get_payment_status(payment_id: uuid.UUID) -> Optional[PaymentOut]:
    """
    Return payment status by payment ID, or None if not found.
    """
    record = payment_repository.get_by_id(payment_id)
    if record is None:
        return None
    return PaymentOut.from_record(record)


def get_payment_by_order(order_id: uuid.UUID) -> Optional[PaymentOut]:
    """
    Return payment status by order ID, or None if no payment exists.
    """
    record = payment_repository.get_by_order_id(order_id)
    if record is None:
        return None
    return PaymentOut.from_record(record)


# Stub — replace when Feat4 order_service is available


def _get_order_amount(order_id: uuid.UUID) -> float:
    """[FEAT4] Stub: replace with order_service.get_order(order_id).total"""
    return 1.0


def _get_customer_id(order_id: uuid.UUID) -> uuid.UUID:
    """[FEAT4] Stub: replace with order_service.get_order(order_id).customer_id"""
    return uuid.uuid4()
