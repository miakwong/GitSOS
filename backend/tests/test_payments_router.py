import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.payment import PaymentOut
from app.schemas.user import UserInDB
from app.dependencies import get_current_user_full

ORDER_ID = uuid.uuid4()
PAYMENT_ID = uuid.uuid4()
CUSTOMER_ID = uuid.uuid4()

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


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user_full] = lambda: MOCK_USER
    yield
    app.dependency_overrides.clear()


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
    response = client.post("/payments/", json={"order_id": str(ORDER_ID)})
    assert response.status_code == 201
    assert response.json()["order_id"] == str(ORDER_ID)


def test_process_payment_duplicate(mock_service):
    mock_service.process_payment.side_effect = ValueError("Payment already exists")
    response = client.post("/payments/", json={"order_id": str(ORDER_ID)})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


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
