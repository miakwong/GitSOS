# services/payment_service.py
# Core payment simulation logic for Feat7
# Order validation is stubbed — replace with real order_service when Feat4 is merged
#
# Public API:
#   process_payment(order_id, customer_id)  → PaymentOut
#   get_payment_status(payment_id)          → PaymentOut

import uuid
from typing import Optional

from app.repositories import payment_repository
from app.schemas.constants import PAYMENT_STATUS_SUCCESS
from app.schemas.payment import PaymentOut, PaymentRecord

class PaymentError(Exception):
    """Raised when a payment cannot be processed."""

def process_payment(order_id: uuid.UUID, customer_id: uuid.UUID) -> PaymentOut:
    """
    Simulate a payment for a confirmed order.

    Raises:
        PaymentError: if a payment already exists for this order.

    Returns:
        PaymentOut: the created payment record.
    """
    # Guard: prevent duplicate payments for the same order
    existing = payment_repository.get_by_order_id(order_id)
    if existing is not None:
        raise PaymentError(f"Payment already exists for order {order_id}")

    # Stub: order amount — replace with order_service.get_order(order_id).total
    # when Feat4 order layer is merged
    amount = _get_order_amount(order_id)

    # Build PaymentRecord directly (repository expects PaymentRecord)
    record = PaymentRecord(
        payment_id=uuid.uuid4(),
        order_id=order_id,
        customer_id=customer_id,
        status=PAYMENT_STATUS_SUCCESS,
        amount=amount,
    )

    saved = payment_repository.create(record)
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
    """
    Stub: returns a fixed amount until order_service is integrated.
    TODO: replace with order_service.get_order(order_id).total
    """
    return 1.0