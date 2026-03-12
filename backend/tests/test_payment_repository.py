# tests/test_payment_repository.py

import uuid
from unittest.mock import patch

import app.repositories.payment_repository as repo
import pytest
from app.schemas.constants import PAYMENT_STATUS_PENDING
from app.schemas.payment import PaymentRecord


@pytest.fixture(autouse=True)
def tmp_db(tmp_path):
    with patch.object(repo, "DATA_PATH", str(tmp_path / "payments.json")):
        yield


def make_record(**kwargs) -> PaymentRecord:
    defaults = {
        "payment_id": uuid.uuid4(),
        "order_id": uuid.uuid4(),
        "customer_id": uuid.uuid4(),
        "status": PAYMENT_STATUS_PENDING,
        "amount": 25.0,
    }
    defaults.update(kwargs)
    return PaymentRecord(**defaults)


# create


def test_create_returns_record():
    r = make_record()
    result = repo.create(r)
    assert result.payment_id == r.payment_id


def test_create_persists_to_file():
    r = make_record()
    repo.create(r)
    assert repo.get_by_id(r.payment_id) is not None


def test_create_appends_not_overwrites():
    repo.create(make_record())
    repo.create(make_record())
    # read back via get to avoid depending on internal _load
    r1 = make_record()
    r2 = make_record()
    repo.create(r1)
    repo.create(r2)
    assert repo.get_by_id(r1.payment_id) is not None
    assert repo.get_by_id(r2.payment_id) is not None


# get_by_id


def test_get_by_id_found():
    r = make_record()
    repo.create(r)
    result = repo.get_by_id(r.payment_id)
    assert result.payment_id == r.payment_id


def test_get_by_id_not_found():
    assert repo.get_by_id(uuid.uuid4()) is None


# get_by_order_id


def test_get_by_order_id_found():
    r = make_record()
    repo.create(r)
    result = repo.get_by_order_id(r.order_id)
    assert result.order_id == r.order_id


def test_get_by_order_id_not_found():
    assert repo.get_by_order_id(uuid.uuid4()) is None


def test_get_by_order_id_correct_among_multiple():
    r1, r2 = make_record(), make_record()
    repo.create(r1)
    repo.create(r2)
    result = repo.get_by_order_id(r2.order_id)
    assert result.payment_id == r2.payment_id


# list_all


def test_list_all_empty():
    assert repo.list_all() == []


def test_list_all_returns_all():
    repo.create(make_record())
    repo.create(make_record())
    assert len(repo.list_all()) == 2


def test_list_all_returns_paymentrecord_instances():
    repo.create(make_record())
    assert all(isinstance(r, PaymentRecord) for r in repo.list_all())
