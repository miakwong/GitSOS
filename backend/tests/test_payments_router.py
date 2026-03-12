# tests/test_payments_router.py
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.payment import PaymentOut

client = TestClient(app)

PAYMENT_ID = uuid4()
ORDER_ID = uuid4()
CUSTOMER_ID = uuid4()

MOCK_PAYMENT_OUT = PaymentOut(
    payment_id=str(PAYMENT_ID),
    order_id=str(ORDER_ID),
    customer_id=str(CUSTOMER_ID),
    status="Success",
    amount=99.9,
    created_at="2025-01-01T00:00:00",
    updated_at=None,
)


@pytest.fixture(autouse=True)
def mock_service():
    with patch("app.routers.payments.payment_service") as m:
        yield m


def test_get_payment_status_found(mock_service):
    mock_service.get_payment_status.return_value = MOCK_PAYMENT_OUT
    response = client.get(f"/payments/{PAYMENT_ID}")
    assert response.status_code == 200
    assert response.json()["payment_id"] == str(PAYMENT_ID)


def test_get_payment_status_not_found(mock_service):
    mock_service.get_payment_status.return_value = None
    response = client.get(f"/payments/{uuid4()}")
    assert response.status_code == 404


def test_get_payment_by_order_found(mock_service):
    mock_service.get_payment_by_order.return_value = MOCK_PAYMENT_OUT
    response = client.get(f"/payments/order/{ORDER_ID}")
    assert response.status_code == 200
    assert response.json()["order_id"] == str(ORDER_ID)


def test_get_payment_by_order_not_found(mock_service):
    mock_service.get_payment_by_order.return_value = None
    response = client.get(f"/payments/order/{uuid4()}")
    assert response.status_code == 404


def test_process_payment_success(mock_service):
    mock_service.process_payment.return_value = MOCK_PAYMENT_OUT
    response = client.post("/payments/", json={"order_id": str(ORDER_ID)})
    assert response.status_code == 201
    assert response.json()["order_id"] == str(ORDER_ID)


def test_process_payment_duplicate(mock_service):
    mock_service.process_payment.side_effect = ValueError("Payment already exists")
    response = client.post("/payments/", json={"order_id": str(ORDER_ID)})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]
