import uuid
from unittest.mock import patch

import pytest
from app.dependencies import get_current_user_full
from app.main import app
from app.schemas.order import DeliveryMethod, Order, OrderStatus
from app.schemas.payment import PaymentOut
from app.schemas.user import UserInDB
from fastapi.testclient import TestClient

ORDER_ID = uuid.uuid4()
PAYMENT_ID = uuid.uuid4()
CUSTOMER_ID = uuid.uuid4()
RESTAURANT_ID = 16

MOCK_USER = UserInDB(
    id=CUSTOMER_ID,
    email="test@example.com",
    role="customer",
    password_hash="hashed",
)

MOCK_PAYMENT = PaymentOut(
    payment_id=str(PAYMENT_ID),
    order_id=str(ORDER_ID),
    customer_id=str(CUSTOMER_ID),
    status="Success",
    amount=49.99,
    created_at="2025-01-01T00:00:00",
    updated_at=None,
)

MOCK_ORDER = Order(
    order_id=ORDER_ID,
    customer_id=str(CUSTOMER_ID),
    restaurant_id=RESTAURANT_ID,
    food_item="Tacos",
    order_value=49.99,
    delivery_distance=5.0,
    delivery_method=DeliveryMethod.BIKE,
    traffic_condition="Low",
    weather_condition="Sunny",
    order_time="2025-01-01T00:00:00",
    order_status=OrderStatus.PLACED,
)


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user_full] = lambda: MOCK_USER
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_notif():
    with patch("app.routers.payments._notif_service"):
        yield


@pytest.fixture
def mock_service():
    with patch("app.routers.payments.payment_service") as mock:
        yield mock


client = TestClient(app)


def test_get_payment_status_found(mock_service):
    mock_service.get_payment_status.return_value = MOCK_PAYMENT
    response = client.get(f"/payments/{PAYMENT_ID}")
    assert response.status_code == 200
    assert response.json()["payment_id"] == str(PAYMENT_ID)


def test_get_payment_status_not_found(mock_service):
    mock_service.get_payment_status.return_value = None
    response = client.get(f"/payments/{PAYMENT_ID}")
    assert response.status_code == 404


def test_get_payment_by_order_found(mock_service):
    mock_service.get_payment_by_order.return_value = MOCK_PAYMENT
    response = client.get(f"/payments/order/{ORDER_ID}")
    assert response.status_code == 200
    assert response.json()["order_id"] == str(ORDER_ID)


def test_get_payment_by_order_not_found(mock_service):
    mock_service.get_payment_by_order.return_value = None
    response = client.get(f"/payments/order/{ORDER_ID}")
    assert response.status_code == 404


def test_process_payment_success(mock_service):
    mock_service.process_payment.return_value = MOCK_PAYMENT
    with patch(
        "app.routers.payments._order_service.get_order", return_value=MOCK_ORDER
    ):
        response = client.post("/payments/", json={"order_id": str(ORDER_ID)})
    assert response.status_code == 201
    assert response.json()["order_id"] == str(ORDER_ID)


def test_process_payment_duplicate(mock_service):
    mock_service.process_payment.side_effect = ValueError("Payment already exists")
    with patch(
        "app.routers.payments._order_service.get_order", return_value=MOCK_ORDER
    ):
        response = client.post("/payments/", json={"order_id": str(ORDER_ID)})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_process_payment_forbidden(mock_service):
    """customer cannot process payment for another customer's order"""
    other_order = MOCK_ORDER.model_copy(update={"customer_id": str(uuid.uuid4())})
    with patch(
        "app.routers.payments._order_service.get_order", return_value=other_order
    ):
        response = client.post("/payments/", json={"order_id": str(ORDER_ID)})
    assert response.status_code == 403


def test_admin_can_process_any_payment(mock_service):
    """admin can process payment regardless of order ownership"""
    admin_user = UserInDB(
        id=uuid.uuid4(),
        email="admin@example.com",
        role="admin",
        password_hash="hashed",
    )
    app.dependency_overrides[get_current_user_full] = lambda: admin_user
    mock_service.process_payment.return_value = MOCK_PAYMENT
    response = client.post("/payments/", json={"order_id": str(ORDER_ID)})
    assert response.status_code == 201


def test_get_payment_status_forbidden(mock_service):
    """customer cannot view another customer's payment"""
    other_payment = PaymentOut(
        payment_id=str(PAYMENT_ID),
        order_id=str(ORDER_ID),
        customer_id=str(uuid.uuid4()),  # different customer
        status="Success",
        amount=10.0,
        created_at="2025-01-01T00:00:00",
    )
    mock_service.get_payment_status.return_value = other_payment
    response = client.get(f"/payments/{PAYMENT_ID}")
    assert response.status_code == 403


def test_admin_can_view_any_payment(mock_service):
    """admin can view any payment regardless of customer_id"""
    admin_user = UserInDB(
        id=uuid.uuid4(),
        email="admin@example.com",
        role="admin",
        password_hash="hashed",
    )
    app.dependency_overrides[get_current_user_full] = lambda: admin_user

    other_payment = PaymentOut(
        payment_id=str(PAYMENT_ID),
        order_id=str(ORDER_ID),
        customer_id=str(uuid.uuid4()),
        status="Success",
        amount=10.0,
        created_at="2025-01-01T00:00:00",
    )
    mock_service.get_payment_status.return_value = other_payment
    response = client.get(f"/payments/{PAYMENT_ID}")
    assert response.status_code == 200


def test_owner_can_view_own_restaurant_payment(mock_service):
    """owner can view payment for an order belonging to their restaurant"""
    owner_user = UserInDB(
        id=uuid.uuid4(),
        email="owner@example.com",
        role="owner",
        password_hash="hashed",
        restaurant_id=RESTAURANT_ID,
    )
    app.dependency_overrides[get_current_user_full] = lambda: owner_user
    mock_service.get_payment_status.return_value = MOCK_PAYMENT
    with patch(
        "app.routers.payments._order_service.get_order", return_value=MOCK_ORDER
    ):
        response = client.get(f"/payments/{PAYMENT_ID}")
    assert response.status_code == 200


def test_owner_cannot_view_other_restaurant_payment(mock_service):
    """owner cannot view payment for an order from a different restaurant"""
    owner_user = UserInDB(
        id=uuid.uuid4(),
        email="owner@example.com",
        role="owner",
        password_hash="hashed",
        restaurant_id=999,
    )
    app.dependency_overrides[get_current_user_full] = lambda: owner_user
    mock_service.get_payment_status.return_value = MOCK_PAYMENT
    with patch(
        "app.routers.payments._order_service.get_order", return_value=MOCK_ORDER
    ):
        response = client.get(f"/payments/{PAYMENT_ID}")
    assert response.status_code == 403
