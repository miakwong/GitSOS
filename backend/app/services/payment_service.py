import uuid

from app.repositories import payment_repository
from app.schemas.constants import PAYMENT_REQUIRED_ORDER_STATUS, PAYMENT_STATUS_SUCCESS
from app.schemas.payment import PaymentCreate, PaymentOut, PaymentRecord
from app.services.order_service import OrderService

PaymentError = ValueError

_order_service = OrderService()


def process_payment(payload: PaymentCreate) -> PaymentOut:
    order_id = payload.order_id

    # Check for duplicate
    existing = payment_repository.get_by_order_id(order_id)
    if existing is not None:
        raise PaymentError(f"Payment already exists for order {order_id}")

    # [FEAT4] Get order details from order service
    order = _order_service.get_order(str(order_id))

    # Order must be in Placed status before payment can be initiated
    if order.order_status.value != PAYMENT_REQUIRED_ORDER_STATUS:
        raise PaymentError(
            f"Payment can only be initiated for orders in '{PAYMENT_REQUIRED_ORDER_STATUS}' status. "
            f"Current status: '{order.order_status.value}'"
        )

    amount = order.order_value
    customer_id = uuid.UUID(order.customer_id)

    record = PaymentRecord(
        payment_id=uuid.uuid4(),
        order_id=order_id,
        customer_id=customer_id,
        status=PAYMENT_STATUS_SUCCESS,
        amount=amount,
    )
    saved = payment_repository.create(record)
    return PaymentOut.from_record(saved)


def get_payment_status(payment_id: uuid.UUID) -> PaymentOut | None:
    record = payment_repository.get_by_id(payment_id)
    if record is None:
        return None
    return PaymentOut.from_record(record)


def get_payment_by_order(order_id: uuid.UUID) -> PaymentOut | None:
    record = payment_repository.get_by_order_id(order_id)
    if record is None:
        return None
    return PaymentOut.from_record(record)


def refund_payment(order_id: uuid.UUID) -> PaymentOut | None:
    existing = payment_repository.get_by_order_id(order_id)
    if existing is None:
        return None

    if existing.status == PAYMENT_STATUS_REFUNDED:
        raise PaymentError(f"Payment for order {order_id} has already been refunded")

    # Update the payment status to Refunded for an order
    updated = payment_repository.update_status(order_id, PAYMENT_STATUS_REFUNDED)
    if updated is None:
        raise PaymentError(f"Failed to process refund for order {order_id}")

    return PaymentOut.from_record(updated)
