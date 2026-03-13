import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from app.schemas.constants import (
    NOTIF_ORDER_CREATED,
    NOTIF_ORDER_STATUS_CHANGED,
    NOTIF_PAYMENT_STATUS_CHANGED,
    PAYMENT_STATUS_SUCCESS,
)
from app.schemas.order import (
    DeliveryMethod,
    Order,
    OrderStatus,
    TrafficCondition,
    WeatherCondition,
)
from app.schemas.payment import PaymentRecord
from app.services.notification_service import NotificationService

ORDER_ID = uuid.uuid4()
CUSTOMER_ID = uuid.uuid4()
OWNER_ID = uuid.uuid4()
RESTAURANT_ID = 1

MOCK_ORDER = Order(
    order_id=ORDER_ID,
    customer_id=str(CUSTOMER_ID),
    restaurant_id=RESTAURANT_ID,
    food_item="Burger",
    order_time=datetime(2025, 1, 1),
    order_value=20.0,
    delivery_distance=5.0,
    delivery_method=DeliveryMethod.CAR,
    traffic_condition=TrafficCondition.LOW,
    weather_condition=WeatherCondition.SUNNY,
    order_status=OrderStatus.PLACED,
)

MOCK_PAYMENT = PaymentRecord(
    payment_id=uuid.uuid4(),
    order_id=ORDER_ID,
    customer_id=CUSTOMER_ID,
    status=PAYMENT_STATUS_SUCCESS,
    amount=20.0,
)


@pytest.fixture(autouse=True)
def mock_repo():
    with patch("app.services.notification_service.notification_repository") as mock:
        mock.create.side_effect = lambda r: r
        yield mock


@pytest.fixture
def service():
    mock_user_repo = MagicMock()
    mock_user_repo.list_users.return_value = []
    return NotificationService(user_repo=mock_user_repo)


@pytest.fixture
def service_with_owner():
    mock_owner = MagicMock()
    mock_owner.role = "owner"
    mock_owner.restaurant_id = RESTAURANT_ID
    mock_owner.id = OWNER_ID
    mock_user_repo = MagicMock()
    mock_user_repo.list_users.return_value = [mock_owner]
    return NotificationService(user_repo=mock_user_repo)


# notify_order_created


def test_notify_order_created_notifies_customer(mock_repo, service):
    service.notify_order_created(MOCK_ORDER)
    user_ids = [c.args[0].user_id for c in mock_repo.create.call_args_list]
    assert CUSTOMER_ID in user_ids


def test_notify_order_created_type_is_correct(mock_repo, service):
    service.notify_order_created(MOCK_ORDER)
    types = [c.args[0].type for c in mock_repo.create.call_args_list]
    assert all(t == NOTIF_ORDER_CREATED for t in types)


def test_notify_order_created_without_owner_one_notification(mock_repo, service):
    service.notify_order_created(MOCK_ORDER)
    assert mock_repo.create.call_count == 1


def test_notify_order_created_with_owner_two_notifications(
    mock_repo, service_with_owner
):
    service_with_owner.notify_order_created(MOCK_ORDER)
    assert mock_repo.create.call_count == 2
    user_ids = [c.args[0].user_id for c in mock_repo.create.call_args_list]
    assert CUSTOMER_ID in user_ids
    assert OWNER_ID in user_ids


# notify_order_status_changed


def test_notify_order_status_changed_notifies_customer(mock_repo, service):
    service.notify_order_status_changed(MOCK_ORDER)
    user_ids = [c.args[0].user_id for c in mock_repo.create.call_args_list]
    assert CUSTOMER_ID in user_ids


def test_notify_order_status_changed_type(mock_repo, service):
    service.notify_order_status_changed(MOCK_ORDER)
    types = [c.args[0].type for c in mock_repo.create.call_args_list]
    assert all(t == NOTIF_ORDER_STATUS_CHANGED for t in types)


def test_notify_order_status_changed_with_owner(mock_repo, service_with_owner):
    service_with_owner.notify_order_status_changed(MOCK_ORDER)
    assert mock_repo.create.call_count == 2


# notify_payment_status


def test_notify_payment_status_notifies_customer(mock_repo, service):
    service.notify_payment_status(MOCK_PAYMENT)
    call = mock_repo.create.call_args
    assert call.args[0].user_id == CUSTOMER_ID


def test_notify_payment_status_type(mock_repo, service):
    service.notify_payment_status(MOCK_PAYMENT)
    call = mock_repo.create.call_args
    assert call.args[0].type == NOTIF_PAYMENT_STATUS_CHANGED


def test_notify_payment_status_one_notification(mock_repo, service):
    service.notify_payment_status(MOCK_PAYMENT)
    assert mock_repo.create.call_count == 1
