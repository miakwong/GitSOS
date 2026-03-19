import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.repositories.order_repository import KaggleOrderRepository, OrderRepository
from app.schemas.order import (
    DeliveryMethod,
    Order,
    OrderStatus,
    TrafficCondition,
    WeatherCondition,
)
from app.schemas.user import UserInDB
from app.services.delivery_service import DeliveryService


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
        f.write("kaggle-002,30,cust-456,Pasta,18.00,2024-01-01T11:00:00,7.0,40.0,5.0\n")
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


def insert_order(order_repo: OrderRepository, customer_id: str, restaurant_id: int = 16) -> Order:
    order = Order(
        order_id=uuid.uuid4(),
        customer_id=customer_id,
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


class TestCustomerListAccess:

    def test_customer_sees_only_own_orders(self, delivery_service, order_repo):
        customer = make_customer()
        other_id = str(uuid.uuid4())
        own_order = insert_order(order_repo, str(customer.id))
        insert_order(order_repo, other_id)

        results = delivery_service.list_delivery_records(customer)

        assert len(results) == 1
        assert results[0].order_id == str(own_order.order_id)

    def test_customer_gets_empty_list_with_no_orders(self, delivery_service):
        customer = make_customer()

        results = delivery_service.list_delivery_records(customer)

        assert results == []

    def test_customer_sees_no_kaggle_orders(self, delivery_service, order_repo):
        customer = make_customer()
        insert_order(order_repo, str(customer.id))

        results = delivery_service.list_delivery_records(customer)

        assert all(r.is_historical is False for r in results)

    def test_customer_result_has_correct_fields(self, delivery_service, order_repo):
        customer = make_customer()
        insert_order(order_repo, str(customer.id))

        results = delivery_service.list_delivery_records(customer)

        r = results[0]
        assert r.delivery_distance == 5.0
        assert r.delivery_method == "Bike"
        assert r.traffic_condition == "Low"
        assert r.weather_condition == "Sunny"
        assert r.is_historical is False


class TestOwnerListAccess:

    def test_owner_sees_own_restaurant_system_orders(self, delivery_service, order_repo):
        owner = make_owner(restaurant_id=16)
        insert_order(order_repo, str(uuid.uuid4()), restaurant_id=16)
        insert_order(order_repo, str(uuid.uuid4()), restaurant_id=30)

        results = delivery_service.list_delivery_records(owner)

        system_orders = [r for r in results if not r.is_historical]
        assert len(system_orders) == 1

    def test_owner_sees_own_restaurant_kaggle_orders(self, delivery_service):
        owner = make_owner(restaurant_id=16)

        results = delivery_service.list_delivery_records(owner)

        kaggle_orders = [r for r in results if r.is_historical]
        assert len(kaggle_orders) == 1
        assert kaggle_orders[0].order_id == "kaggle-001"

    def test_owner_does_not_see_other_restaurant_kaggle(self, delivery_service):
        owner = make_owner(restaurant_id=16)

        results = delivery_service.list_delivery_records(owner)

        ids = [r.order_id for r in results]
        assert "kaggle-002" not in ids

    def test_owner_gets_empty_for_no_matching_orders(self, delivery_service, order_repo):
        owner = make_owner(restaurant_id=99)
        insert_order(order_repo, str(uuid.uuid4()), restaurant_id=16)

        results = delivery_service.list_delivery_records(owner)

        assert results == []

    def test_owner_sees_both_system_and_kaggle(self, delivery_service, order_repo):
        owner = make_owner(restaurant_id=16)
        insert_order(order_repo, str(uuid.uuid4()), restaurant_id=16)

        results = delivery_service.list_delivery_records(owner)

        assert any(r.is_historical is False for r in results)
        assert any(r.is_historical is True for r in results)


class TestAdminListAccess:

    def test_admin_sees_all_system_orders(self, delivery_service, order_repo):
        admin = make_admin()
        insert_order(order_repo, str(uuid.uuid4()), restaurant_id=16)
        insert_order(order_repo, str(uuid.uuid4()), restaurant_id=30)

        results = delivery_service.list_delivery_records(admin)

        system_orders = [r for r in results if not r.is_historical]
        assert len(system_orders) == 2

    def test_admin_sees_all_kaggle_orders(self, delivery_service):
        admin = make_admin()

        results = delivery_service.list_delivery_records(admin)

        kaggle_orders = [r for r in results if r.is_historical]
        assert len(kaggle_orders) == 2

    def test_admin_sees_combined_system_and_kaggle(self, delivery_service, order_repo):
        admin = make_admin()
        insert_order(order_repo, str(uuid.uuid4()))

        results = delivery_service.list_delivery_records(admin)

        assert any(r.is_historical is False for r in results)
        assert any(r.is_historical is True for r in results)

    def test_admin_gets_empty_list_when_no_orders(self, temp_orders_file, temp_kaggle_csv):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(
                "order_id,restaurant_id,customer_id,food_item,"
                "order_value,order_time,delivery_distance,"
                "delivery_time_actual,delivery_delay\n"
            )
            empty_csv = Path(f.name)
        svc = DeliveryService(
            order_repo=OrderRepository(orders_path=temp_orders_file),
            kaggle_repo=KaggleOrderRepository(csv_path=empty_csv),
        )
        admin = make_admin()

        results = svc.list_delivery_records(admin)

        assert results == []
