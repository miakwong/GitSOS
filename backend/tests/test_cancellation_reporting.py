import uuid
from unittest.mock import patch

import pytest
from app.dependencies import get_current_admin, get_current_owner
from app.main import app
from app.schemas.constants import PAYMENT_STATUS_REFUNDED, PAYMENT_STATUS_SUCCESS
from app.schemas.order import DeliveryMethod, Order, OrderStatus
from app.schemas.payment import PaymentRecord
from fastapi.testclient import TestClient

client = TestClient(app)

ADMIN_ID = uuid.uuid4()
OWNER_ID = uuid.uuid4()
RESTAURANT_ID = 16


def _make_order(order_status: OrderStatus, restaurant_id: int = RESTAURANT_ID) -> Order:
    return Order(
        order_id=uuid.uuid4(),
        customer_id=str(uuid.uuid4()),
        restaurant_id=restaurant_id,
        food_item="Tacos",
        order_value=25.0,
        delivery_distance=5.0,
        delivery_method=DeliveryMethod.BIKE,
        traffic_condition="Low",
        weather_condition="Sunny",
        order_time="2025-01-01T00:00:00",
        order_status=order_status,
    )


def _make_payment(status: str) -> PaymentRecord:
    return PaymentRecord(
        payment_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        status=status,
        amount=25.0,
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.pop(get_current_admin, None)
    app.dependency_overrides.pop(get_current_owner, None)


@pytest.fixture
def as_admin():
    app.dependency_overrides[get_current_admin] = lambda: ADMIN_ID


@pytest.fixture
def as_owner():
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, RESTAURANT_ID)



@pytest.mark.usefixtures("as_admin")
def test_admin_cancelled_orders_returns_only_cancelled():
    # This is the mix of cancelled and non-cancelled orders, which only cancelled should be returned
    orders = [
        _make_order(OrderStatus.CANCELLED),
        _make_order(OrderStatus.PLACED),
        _make_order(OrderStatus.CANCELLED),
    ]
    with patch("app.routers.orders.order_service") as mock_svc:
        mock_svc.get_all_orders.return_value = orders
        response = client.get("/orders/admin/cancelled")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(o["order_status"] == "Cancelled" for o in data)


@pytest.mark.usefixtures("as_admin")
def test_admin_cancelled_orders_empty_when_none_cancelled():
    # If there are no cancelled orders then the system should return empty list, not an error
    orders = [_make_order(OrderStatus.PLACED), _make_order(OrderStatus.PAID)]
    with patch("app.routers.orders.order_service") as mock_svc:
        mock_svc.get_all_orders.return_value = orders
        response = client.get("/orders/admin/cancelled")
    assert response.status_code == 200
    assert response.json() == []


def test_admin_cancelled_orders_requires_admin_auth():
    # If there is no auth override, it should be denied
    response = client.get("/orders/admin/cancelled")
    assert response.status_code == 401 or response.status_code == 403


@pytest.mark.usefixtures("as_owner")
def test_owner_cancelled_orders_returns_only_their_cancelled():
    # Owner should only see cancelled orders from their own restaurant
    orders = [
        _make_order(OrderStatus.CANCELLED, restaurant_id=RESTAURANT_ID),
        _make_order(OrderStatus.PLACED, restaurant_id=RESTAURANT_ID),
        _make_order(OrderStatus.CANCELLED, restaurant_id=RESTAURANT_ID),
    ]
    with patch("app.routers.orders.order_service") as mock_svc:
        mock_svc.get_orders_for_owner.return_value = orders
        response = client.get("/orders/owner/cancelled")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(o["order_status"] == "Cancelled" for o in data)


@pytest.mark.usefixtures("as_owner")
def test_owner_cancelled_orders_empty_when_none_cancelled():
    orders = [_make_order(OrderStatus.PLACED, restaurant_id=RESTAURANT_ID)]
    with patch("app.routers.orders.order_service") as mock_svc:
        mock_svc.get_orders_for_owner.return_value = orders
        response = client.get("/orders/owner/cancelled")
    assert response.status_code == 200
    assert response.json() == []


def test_owner_cancelled_orders_requires_owner_auth():
    # If there is no auth override, it should be denied
    response = client.get("/orders/owner/cancelled")
    assert response.status_code == 401 or response.status_code == 403


@pytest.mark.usefixtures("as_admin")
def test_admin_refunds_returns_only_refunded_payments():
    # This is the mix of payment statuses, which only Refunded should be returned
    payments = [
        _make_payment(PAYMENT_STATUS_REFUNDED),
        _make_payment(PAYMENT_STATUS_SUCCESS),
        _make_payment(PAYMENT_STATUS_REFUNDED),
    ]
    with patch("app.services.payment_service.payment_repository") as mock_repo:
        mock_repo.list_all.return_value = payments
        response = client.get("/payments/admin/refunds")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(p["status"] == PAYMENT_STATUS_REFUNDED for p in data)


@pytest.mark.usefixtures("as_admin")
def test_admin_refunds_empty_when_none_refunded():
    # If there are no refunded payments then the system should return empty list, not an error
    payments = [_make_payment(PAYMENT_STATUS_SUCCESS)]
    with patch("app.services.payment_service.payment_repository") as mock_repo:
        mock_repo.list_all.return_value = payments
        response = client.get("/payments/admin/refunds")
    assert response.status_code == 200
    assert response.json() == []


def test_admin_refunds_requires_admin_auth():
    # If there is no auth override, it should be denied
    response = client.get("/payments/admin/refunds")
    assert response.status_code == 401 or response.status_code == 403
