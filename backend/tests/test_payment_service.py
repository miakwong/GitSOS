import uuid
from unittest.mock import patch, MagicMock

import pytest

from app.schemas.constants import PAYMENT_STATUS_SUCCESS
from app.schemas.order import Order, OrderStatus, DeliveryMethod, TrafficCondition, WeatherCondition
from app.schemas.payment import PaymentCreate, PaymentOut, PaymentRecord
import app.services.payment_service as service
from datetime import datetime

ORDER_ID = uuid.uuid4()
CUSTOMER_ID = uuid.uuid4()
PAYMENT_ID = uuid.uuid4()


def _make_record(**overrides) -> PaymentRecord:
    base = dict(
        payment_id=PAYMENT_ID,
        order_id=ORDER_ID,
        customer_id=CUSTOMER_ID,
        status=PAYMENT_STATUS_SUCCESS,
        amount=49.99,
    )
    base.update(overrides)
    return PaymentRecord(**base)


def _make_order() -> Order:
    return Order(
        order_id=ORDER_ID,
        customer_id=str(CUSTOMER_ID),
        restaurant_id=1,
        food_item="Burger",
        order_time=datetime(2025, 1, 1),
        order_value=49.99,
        delivery_distance=5.0,
        delivery_method=DeliveryMethod.CAR,
        traffic_condition=TrafficCondition.LOW,
        weather_condition=WeatherCondition.SUNNY,
        order_status=OrderStatus.PLACED,
    )


@pytest.fixture(autouse=True)
def mock_repo():
    with patch("app.services.payment_service.payment_repository") as mock:
        mock.get_by_order_id.return_value = None
        mock.get_by_id.return_value = None
        mock.create.side_effect = lambda r: r
        yield mock


@pytest.fixture(autouse=True)
def mock_order_service():
    with patch("app.services.payment_service._order_service") as mock:
        mock.get_order.return_value = _make_order()
        yield mock


# process_payment

def test_process_payment_returns_payment_out(mock_repo, mock_order_service):
    result = service.process_payment(PaymentCreate(order_id=ORDER_ID))
    assert isinstance(result, PaymentOut)


def test_process_payment_status_is_success(mock_repo, mock_order_service):
    result = service.process_payment(PaymentCreate(order_id=ORDER_ID))
    assert result.status == PAYMENT_STATUS_SUCCESS


def test_process_payment_order_id_matches(mock_repo, mock_order_service):
    result = service.process_payment(PaymentCreate(order_id=ORDER_ID))
    assert result.order_id == str(ORDER_ID)


def test_process_payment_customer_id_matches(mock_repo, mock_order_service):
    result = service.process_payment(PaymentCreate(order_id=ORDER_ID))
    assert result.customer_id == str(CUSTOMER_ID)


def test_process_payment_amount_from_order(mock_repo, mock_order_service):
    result = service.process_payment(PaymentCreate(order_id=ORDER_ID))
    assert result.amount == 49.99


def test_process_payment_calls_repository_create(mock_repo, mock_order_service):
    service.process_payment(PaymentCreate(order_id=ORDER_ID))
    mock_repo.create.assert_called_once()


def test_process_payment_raises_if_payment_exists(mock_repo, mock_order_service):
    mock_repo.get_by_order_id.return_value = _make_record()
    with pytest.raises(service.PaymentError):
        service.process_payment(PaymentCreate(order_id=ORDER_ID))


def test_process_payment_no_duplicate_create_when_exists(mock_repo, mock_order_service):
    mock_repo.get_by_order_id.return_value = _make_record()
    with pytest.raises(service.PaymentError):
        service.process_payment(PaymentCreate(order_id=ORDER_ID))
    mock_repo.create.assert_not_called()


# get_payment_status

def test_get_payment_status_found(mock_repo):
    mock_repo.get_by_id.return_value = _make_record()
    result = service.get_payment_status(PAYMENT_ID)
    assert result is not None


def test_get_payment_status_not_found(mock_repo):
    mock_repo.get_by_id.return_value = None
    assert service.get_payment_status(PAYMENT_ID) is None


def test_get_payment_status_correct_payment_id(mock_repo):
    mock_repo.get_by_id.return_value = _make_record()
    result = service.get_payment_status(PAYMENT_ID)
    assert result.payment_id == str(PAYMENT_ID)


# get_payment_by_order

def test_get_payment_by_order_found(mock_repo):
    mock_repo.get_by_order_id.return_value = _make_record()
    result = service.get_payment_by_order(ORDER_ID)
    assert result is not None


def test_get_payment_by_order_not_found(mock_repo):
    mock_repo.get_by_order_id.return_value = None
    assert service.get_payment_by_order(ORDER_ID) is None


def test_get_payment_by_order_correct_order_id(mock_repo):
    mock_repo.get_by_order_id.return_value = _make_record()
    result = service.get_payment_by_order(ORDER_ID)
    assert result.order_id == str(ORDER_ID)
