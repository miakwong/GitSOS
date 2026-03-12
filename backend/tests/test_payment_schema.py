#Tests for app/schemas/payment.py
import pytest
from uuid import uuid4
from unittest.mock import patch

from app.schemas.payment import PaymentCreate, PaymentRecord, PaymentOut
from app.schemas.constants import (
    PAYMENT_STATUS_PENDING,
    PAYMENT_STATUS_SUCCESS,
    PAYMENT_STATUS_FAILED,
    VALID_PAYMENT_STATUSES,
)

FIXED_TIME = "2025-01-01T00:00:00"

# Shared test UUIDs 
MOCK_USER_ID = uuid4()
MOCK_ORDER_ID = uuid4()
MOCK_PAYMENT_ID = uuid4()

# PaymentCreate Tests

def test_payment_create_valid_order_id():
    p = PaymentCreate(order_id=MOCK_ORDER_ID)
    assert p.order_id == MOCK_ORDER_ID

def test_payment_create_requires_order_id():
    with pytest.raises(Exception):
        PaymentCreate()

# PaymentRecord Tests

def _make_record(**overrides):
    """Helper: build a minimal valid PaymentRecord."""
    defaults = dict(
        payment_id=MOCK_PAYMENT_ID,
        order_id=MOCK_ORDER_ID,
        customer_id=MOCK_USER_ID,   # customer_id = user UUID
        amount=100.0,
    )
    return PaymentRecord(**{**defaults, **overrides})


def test_payment_record_default_status_is_pending():
    record = _make_record()
    assert record.status == PAYMENT_STATUS_PENDING


def test_payment_record_accepts_all_valid_statuses():
    for status in VALID_PAYMENT_STATUSES:
        record = _make_record(status=status)
        assert record.status == status


def test_payment_record_rejects_invalid_status():
    with pytest.raises(Exception):
        _make_record(status="Cooking")


def test_payment_record_rejects_zero_amount():
    with pytest.raises(Exception):
        _make_record(amount=0)


def test_payment_record_rejects_negative_amount():
    with pytest.raises(Exception):
        _make_record(amount=-5.0)


def test_payment_record_created_at_mocked():
    with patch("app.schemas.payment.datetime") as mock_dt:
        mock_dt.now.return_value.isoformat.return_value = FIXED_TIME
        record = _make_record()

    assert record.created_at == FIXED_TIME


def test_payment_record_updated_at_defaults_to_none():
    record = _make_record()
    assert record.updated_at is None


# PaymentOut Tests 
def test_payment_out_from_record_converts_uuids_to_str():
    record = _make_record(status=PAYMENT_STATUS_SUCCESS)
    out = PaymentOut.from_record(record)

    assert out.payment_id == str(MOCK_PAYMENT_ID)
    assert out.order_id == str(MOCK_ORDER_ID)
    assert out.customer_id == str(MOCK_USER_ID)


def test_payment_out_from_record_preserves_fields():
    record = _make_record(amount=42.5, status=PAYMENT_STATUS_FAILED)
    out = PaymentOut.from_record(record)

    assert out.amount == 42.5
    assert out.status == PAYMENT_STATUS_FAILED
    assert out.updated_at is None
