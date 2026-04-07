import uuid
from pathlib import Path

from app.repositories import notification_repository
from app.repositories.user_repository import UserRepository
from app.schemas.constants import (
    NOTIF_ORDER_CREATED,
    NOTIF_ORDER_STATUS_CHANGED,
    NOTIF_PAYMENT_STATUS_CHANGED,
    ROLE_OWNER,
)
from app.schemas.notification import NotificationRecord
from app.schemas.order import Order
from app.schemas.payment import PaymentOut, PaymentRecord


class NotificationService:
    def __init__(self, user_repo=None):
        _users_file = Path(__file__).resolve().parent.parent / "data" / "users.json"
        self._user_repo = user_repo or UserRepository(_users_file)

    def _create(
        self, user_id: uuid.UUID, order_id: uuid.UUID, notif_type: str, message: str
    ) -> NotificationRecord:
        record = NotificationRecord(
            notification_id=uuid.uuid4(),
            user_id=user_id,
            order_id=order_id,
            type=notif_type,
            message=message,
        )
        return notification_repository.create(record)

    def _find_owner_for_restaurant(self, restaurant_id: int) -> uuid.UUID | None:
        for user in self._user_repo.list_users():
            if user.role == ROLE_OWNER and user.restaurant_id == restaurant_id:
                return user.id
        return None

    @staticmethod
    def _parse_uuid(value: str) -> uuid.UUID | None:
        try:
            return uuid.UUID(str(value))
        except (ValueError, AttributeError):
            return None

    def notify_order_created(self, order: Order) -> None:
        customer_id = self._parse_uuid(order.customer_id)
        if customer_id is None:
            return
        self._create(
            customer_id,
            order.order_id,
            NOTIF_ORDER_CREATED,
            f"Your order for {order.food_item} has been placed.",
        )
        owner_id = self._find_owner_for_restaurant(order.restaurant_id)
        if owner_id:
            self._create(
                owner_id,
                order.order_id,
                NOTIF_ORDER_CREATED,
                f"New order for {order.food_item} received at your restaurant.",
            )

    def notify_order_status_changed(self, order: Order) -> None:
        customer_id = self._parse_uuid(order.customer_id)
        if customer_id is None:
            return
        self._create(
            customer_id,
            order.order_id,
            NOTIF_ORDER_STATUS_CHANGED,
            f"Your {order.food_item} order is now {order.order_status.value}.",
        )
        owner_id = self._find_owner_for_restaurant(order.restaurant_id)
        if owner_id:
            self._create(
                owner_id,
                order.order_id,
                NOTIF_ORDER_STATUS_CHANGED,
                f"{order.food_item} order is now {order.order_status.value}.",
            )

    def notify_payment_status(self, payment: PaymentRecord) -> None:
        self._create(
            payment.customer_id,
            payment.order_id,
            NOTIF_PAYMENT_STATUS_CHANGED,
            f"Your payment of ${payment.amount:.2f} is {payment.status}.",
        )

    def notify_payment_out(self, payment: PaymentOut) -> None:
        self._create(
            uuid.UUID(payment.customer_id),
            uuid.UUID(payment.order_id),
            NOTIF_PAYMENT_STATUS_CHANGED,
            f"Your payment of ${payment.amount:.2f} is {payment.status}.",
        )
