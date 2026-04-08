import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.repositories.order_repository import KaggleOrderRepository, OrderRepository
from app.schemas.delivery import DeliveryOutcomeCreate
from app.schemas.order import (
    DeliveryMethod,
    Order,
    OrderStatus,
    TrafficCondition,
    WeatherCondition,
)
from app.schemas.user import UserInDB
from app.services.delivery_service import DeliveryService

# tests for recording delivery outcomes, covering authentication, authorization, validation, and business rules around when outcomes can be recorded and how they affect order data
def make_customer(uid: str = None) -> UserInDB:
    return UserInDB(
        id=uuid.UUID(uid) if uid else uuid.uuid4(),
        email="cust@test.com",
        role="customer",
        password_hash="hashed",
    )


def make_owner(restaurant_id: int = 16) -> UserInDB:
    return UserInDB(
        id=uuid.uuid4(),
        email="owner@test.com",
        role="owner",
        password_hash="hashed",
        restaurant_id=restaurant_id,
    )


def make_admin() -> UserInDB:
    return UserInDB(
        id=uuid.uuid4(),
        email="admin@test.com",
        role="admin",
        password_hash="hashed",
    )


@pytest.fixture
def temp_orders_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([], f)
        return Path(f.name)


@pytest.fixture
def temp_kaggle_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(
            "order_id,restaurant_id,customer_id,food_item,"
            "order_value,order_time,delivery_distance,"
            "delivery_time_actual,delivery_delay\n"
        )
        f.write("kaggle-001,16,cust-123,Taccos,25.50,2024-01-01T10:00:00,5.0,30.0,0.0\n")
        return Path(f.name)


@pytest.fixture
def order_repo(temp_orders_file):
    return OrderRepository(orders_path=temp_orders_file)


@pytest.fixture
def kaggle_repo(temp_kaggle_csv):
    return KaggleOrderRepository(csv_path=temp_kaggle_csv)


@pytest.fixture
def delivery_service(order_repo, kaggle_repo):
    return DeliveryService(order_repo=order_repo, kaggle_repo=kaggle_repo)


def insert_order(order_repo: OrderRepository, restaurant_id: int = 16, customer_id: str = None) -> Order:
    order = Order(
        order_id=uuid.uuid4(),
        customer_id=customer_id or str(uuid.uuid4()),
        restaurant_id=restaurant_id,
        food_item="Taccos",
        order_time=datetime.now(timezone.utc),
        order_value=25.50,
        delivery_distance=5.0,
        delivery_method=DeliveryMethod.BIKE,
        traffic_condition=TrafficCondition.LOW,
        weather_condition=WeatherCondition.SUNNY,
        order_status=OrderStatus.PLACED,
    )
    raw = order_repo._load_orders()
    raw.append(order.model_dump(mode="json"))
    order_repo._save_orders(raw)
    return order


def set_status(order_repo: OrderRepository, order_id: str, new_status: OrderStatus):
    order_repo.update_order_status(order_id, new_status)


class TestRecordOutcomeSuccess:

    def test_owner_records_outcome_for_delivered_order(self, delivery_service, order_repo):
        owner = make_owner(restaurant_id=16)
        order = insert_order(order_repo, restaurant_id=16)
        set_status(order_repo, str(order.order_id), OrderStatus.DELIVERED)
        outcome = DeliveryOutcomeCreate(actual_delivery_time=35.0, delivery_delay=5.0)

        result = delivery_service.record_delivery_outcome(str(order.order_id), outcome, owner)

        assert result.actual_delivery_time == 35.0
        assert result.delivery_delay == 5.0
        assert result.order_status == OrderStatus.DELIVERED

    def test_admin_records_outcome_for_any_delivered_order(self, delivery_service, order_repo):
        admin = make_admin()
        order = insert_order(order_repo, restaurant_id=30)
        set_status(order_repo, str(order.order_id), OrderStatus.DELIVERED)
        outcome = DeliveryOutcomeCreate(actual_delivery_time=20.0, delivery_delay=0.0)

        result = delivery_service.record_delivery_outcome(str(order.order_id), outcome, admin)

        assert result.actual_delivery_time == 20.0
        assert result.delivery_delay == 0.0

    def test_delivery_params_unchanged_after_outcome_recorded(self, delivery_service, order_repo):
        owner = make_owner(restaurant_id=16)
        order = insert_order(order_repo, restaurant_id=16)
        set_status(order_repo, str(order.order_id), OrderStatus.DELIVERED)
        outcome = DeliveryOutcomeCreate(actual_delivery_time=30.0, delivery_delay=2.0)

        result = delivery_service.record_delivery_outcome(str(order.order_id), outcome, owner)

        # delivery parameters set at creation should be unchanged
        assert result.delivery_distance == 5.0
        assert result.delivery_method == DeliveryMethod.BIKE
        assert result.traffic_condition == TrafficCondition.LOW
        assert result.weather_condition == WeatherCondition.SUNNY

    def test_zero_delivery_delay_is_valid(self, delivery_service, order_repo):
        admin = make_admin()
        order = insert_order(order_repo)
        set_status(order_repo, str(order.order_id), OrderStatus.DELIVERED)
        outcome = DeliveryOutcomeCreate(actual_delivery_time=25.0, delivery_delay=0.0)

        result = delivery_service.record_delivery_outcome(str(order.order_id), outcome, admin)

        assert result.delivery_delay == 0.0

    def test_negative_delivery_delay_is_valid(self, delivery_service, order_repo):
        admin = make_admin()
        order = insert_order(order_repo)
        set_status(order_repo, str(order.order_id), OrderStatus.DELIVERED)
        outcome = DeliveryOutcomeCreate(actual_delivery_time=20.0, delivery_delay=-5.0)

        result = delivery_service.record_delivery_outcome(str(order.order_id), outcome, admin)

        assert result.delivery_delay == -5.0


class TestRecordOutcomeRejected:

    def test_customer_cannot_record_outcome(self, delivery_service, order_repo):
        customer = make_customer()
        order = insert_order(order_repo)
        set_status(order_repo, str(order.order_id), OrderStatus.DELIVERED)
        outcome = DeliveryOutcomeCreate(actual_delivery_time=30.0, delivery_delay=0.0)

        with pytest.raises(HTTPException) as exc:
            delivery_service.record_delivery_outcome(str(order.order_id), outcome, customer)
        assert exc.value.status_code == 403

    def test_owner_blocked_from_other_restaurant_order(self, delivery_service, order_repo):
        owner = make_owner(restaurant_id=16)
        order = insert_order(order_repo, restaurant_id=30)
        set_status(order_repo, str(order.order_id), OrderStatus.DELIVERED)
        outcome = DeliveryOutcomeCreate(actual_delivery_time=30.0, delivery_delay=0.0)

        with pytest.raises(HTTPException) as exc:
            delivery_service.record_delivery_outcome(str(order.order_id), outcome, owner)
        assert exc.value.status_code == 403

    def test_outcome_rejected_for_placed_order(self, delivery_service, order_repo):
        admin = make_admin()
        order = insert_order(order_repo)
        outcome = DeliveryOutcomeCreate(actual_delivery_time=30.0, delivery_delay=0.0)

        with pytest.raises(HTTPException) as exc:
            delivery_service.record_delivery_outcome(str(order.order_id), outcome, admin)
        assert exc.value.status_code == 400
        assert "Delivered" in exc.value.detail

    def test_outcome_rejected_for_paid_order(self, delivery_service, order_repo):
        admin = make_admin()
        order = insert_order(order_repo)
        set_status(order_repo, str(order.order_id), OrderStatus.PAID)
        outcome = DeliveryOutcomeCreate(actual_delivery_time=30.0, delivery_delay=0.0)

        with pytest.raises(HTTPException) as exc:
            delivery_service.record_delivery_outcome(str(order.order_id), outcome, admin)
        assert exc.value.status_code == 400

    def test_outcome_rejected_for_preparing_order(self, delivery_service, order_repo):
        admin = make_admin()
        order = insert_order(order_repo)
        set_status(order_repo, str(order.order_id), OrderStatus.PREPARING)
        outcome = DeliveryOutcomeCreate(actual_delivery_time=30.0, delivery_delay=0.0)

        with pytest.raises(HTTPException) as exc:
            delivery_service.record_delivery_outcome(str(order.order_id), outcome, admin)
        assert exc.value.status_code == 400

    def test_outcome_rejected_for_cancelled_order(self, delivery_service, order_repo):
        admin = make_admin()
        order = insert_order(order_repo)
        set_status(order_repo, str(order.order_id), OrderStatus.CANCELLED)
        outcome = DeliveryOutcomeCreate(actual_delivery_time=30.0, delivery_delay=0.0)

        with pytest.raises(HTTPException) as exc:
            delivery_service.record_delivery_outcome(str(order.order_id), outcome, admin)
        assert exc.value.status_code == 400

    def test_outcome_rejected_for_kaggle_order(self, delivery_service):
        admin = make_admin()
        outcome = DeliveryOutcomeCreate(actual_delivery_time=30.0, delivery_delay=0.0)

        with pytest.raises(HTTPException) as exc:
            delivery_service.record_delivery_outcome("kaggle-001", outcome, admin)
        assert exc.value.status_code == 400
        assert "Kaggle" in exc.value.detail

    def test_outcome_rejected_for_nonexistent_order(self, delivery_service):
        admin = make_admin()
        outcome = DeliveryOutcomeCreate(actual_delivery_time=30.0, delivery_delay=0.0)

        with pytest.raises(HTTPException) as exc:
            delivery_service.record_delivery_outcome(str(uuid.uuid4()), outcome, admin)
        assert exc.value.status_code == 404


class TestOutcomeImmutability:

    def test_outcome_cannot_be_recorded_twice(self, delivery_service, order_repo):
        admin = make_admin()
        order = insert_order(order_repo)
        set_status(order_repo, str(order.order_id), OrderStatus.DELIVERED)
        outcome = DeliveryOutcomeCreate(actual_delivery_time=30.0, delivery_delay=0.0)

        delivery_service.record_delivery_outcome(str(order.order_id), outcome, admin)

        with pytest.raises(HTTPException) as exc:
            delivery_service.record_delivery_outcome(str(order.order_id), outcome, admin)
        assert exc.value.status_code == 400
        assert "already been recorded" in exc.value.detail

    def test_outcome_values_unchanged_after_second_attempt(self, delivery_service, order_repo):
        admin = make_admin()
        order = insert_order(order_repo)
        set_status(order_repo, str(order.order_id), OrderStatus.DELIVERED)
        first = DeliveryOutcomeCreate(actual_delivery_time=30.0, delivery_delay=2.0)
        second = DeliveryOutcomeCreate(actual_delivery_time=99.0, delivery_delay=99.0)

        delivery_service.record_delivery_outcome(str(order.order_id), first, admin)

        with pytest.raises(HTTPException):
            delivery_service.record_delivery_outcome(str(order.order_id), second, admin)

        stored = delivery_service.order_repo.get_order_by_id(str(order.order_id))
        assert stored.actual_delivery_time == 30.0
        assert stored.delivery_delay == 2.0


class TestOutcomeSchemaValidation:

    def test_actual_delivery_time_must_be_positive(self):
        with pytest.raises(Exception):
            DeliveryOutcomeCreate(actual_delivery_time=0.0, delivery_delay=0.0)

    def test_actual_delivery_time_negative_rejected(self):
        with pytest.raises(Exception):
            DeliveryOutcomeCreate(actual_delivery_time=-1.0, delivery_delay=0.0)

    def test_valid_outcome_schema(self):
        outcome = DeliveryOutcomeCreate(actual_delivery_time=25.0, delivery_delay=3.0)
        assert outcome.actual_delivery_time == 25.0
        assert outcome.delivery_delay == 3.0
