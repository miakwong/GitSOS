# Unit tests for DeliveryService
import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.repositories.order_repository import KaggleOrderRepository, OrderRepository
from app.schemas.delivery import DeliveryInfo
from app.schemas.order import (
    DeliveryMethod,
    Order,
    OrderStatus,
    TrafficCondition,
    WeatherCondition,
)
from app.schemas.user import UserInDB
from app.services.delivery_service import DeliveryService


# helpers to build fake user objects for different roles

def make_customer(customer_id: str = None) -> UserInDB:
    uid = uuid.UUID(customer_id) if customer_id else uuid.uuid4()
    return UserInDB(
        id=uid,
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


# shared fixtures

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


# helper to insert a system order directly into the repo

def insert_system_order(order_repo: OrderRepository, customer_id: str, restaurant_id: int = 16) -> Order:
    order = Order(
        order_id=uuid.uuid4(),
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        food_item="Taccos",
        order_time=datetime.now(timezone.utc),
        order_value=25.50,
        delivery_distance=5.0,
        delivery_method=DeliveryMethod.BIKE,
        traffic_condition=TrafficCondition.MEDIUM,
        weather_condition=WeatherCondition.RAINY,
        order_status=OrderStatus.PLACED,
    )
    raw = order_repo._load_orders()
    raw.append(order.model_dump(mode="json"))
    order_repo._save_orders(raw)
    return order


# tests for system order delivery info and access control
class TestDeliveryFromSystemOrder:

    def test_customer_gets_own_order_delivery_info(self, delivery_service, order_repo):
        customer = make_customer()
        order = insert_system_order(order_repo, str(customer.id))

        result = delivery_service.get_delivery_info(str(order.order_id), customer)

        assert isinstance(result, DeliveryInfo)
        assert result.order_id == str(order.order_id)
        assert result.delivery_distance == 5.0
        assert result.delivery_method == "Bike"
        assert result.traffic_condition == "Medium"
        assert result.weather_condition == "Rainy"
        assert result.is_historical is False

    def test_system_order_has_no_kaggle_fields(self, delivery_service, order_repo):
        customer = make_customer()
        order = insert_system_order(order_repo, str(customer.id))

        result = delivery_service.get_delivery_info(str(order.order_id), customer)

        
        assert result.delivery_time is None
        assert result.delivery_delay is None

    def test_customer_blocked_from_another_customers_order(self, delivery_service, order_repo):
        owner_of_order = make_customer()
        other_customer = make_customer()
        order = insert_system_order(order_repo, str(owner_of_order.id))

        with pytest.raises(HTTPException) as exc:
            delivery_service.get_delivery_info(str(order.order_id), other_customer)
        assert exc.value.status_code == 403

    def test_owner_gets_delivery_info_for_their_restaurant_order(self, delivery_service, order_repo):
        customer = make_customer()
        order = insert_system_order(order_repo, str(customer.id), restaurant_id=16)
        owner = make_owner(restaurant_id=16)

        result = delivery_service.get_delivery_info(str(order.order_id), owner)

        assert result.order_id == str(order.order_id)
        assert result.is_historical is False

    def test_owner_blocked_from_different_restaurant_order(self, delivery_service, order_repo):
        customer = make_customer()
        order = insert_system_order(order_repo, str(customer.id), restaurant_id=30)
        owner = make_owner(restaurant_id=16)

        with pytest.raises(HTTPException) as exc:
            delivery_service.get_delivery_info(str(order.order_id), owner)
        assert exc.value.status_code == 403

    def test_admin_gets_any_system_order_delivery_info(self, delivery_service, order_repo):
        customer = make_customer()
        order = insert_system_order(order_repo, str(customer.id), restaurant_id=30)
        admin = make_admin()

        result = delivery_service.get_delivery_info(str(order.order_id), admin)

        assert result.order_id == str(order.order_id)
        assert result.is_historical is False


# tests for Kaggle historical order delivery info and access control
class TestDeliveryFromKaggleOrder:

    def test_owner_gets_kaggle_order_delivery_info(self, delivery_service):
        owner = make_owner(restaurant_id=16)

        result = delivery_service.get_delivery_info("kaggle-001", owner)

        assert result.order_id == "kaggle-001"
        assert result.delivery_distance == 5.0
        assert result.delivery_time == 30.0
        assert result.delivery_delay == 0.0
        assert result.is_historical is True

    def test_kaggle_order_has_no_system_fields(self, delivery_service):
        owner = make_owner(restaurant_id=16)

        result = delivery_service.get_delivery_info("kaggle-001", owner)

        # system-only fields should be absent for Kaggle orders
        assert result.delivery_method is None
        assert result.traffic_condition is None
        assert result.weather_condition is None

    def test_customer_blocked_from_kaggle_order(self, delivery_service):
        customer = make_customer()

        with pytest.raises(HTTPException) as exc:
            delivery_service.get_delivery_info("kaggle-001", customer)
        assert exc.value.status_code == 403

    def test_owner_blocked_from_wrong_restaurant_kaggle_order(self, delivery_service):
        # kaggle-001 belongs to restaurant 16; owner of 30 should be blocked
        owner = make_owner(restaurant_id=30)

        with pytest.raises(HTTPException) as exc:
            delivery_service.get_delivery_info("kaggle-001", owner)
        assert exc.value.status_code == 403

    def test_admin_gets_any_kaggle_order_delivery_info(self, delivery_service):
        admin = make_admin()

        result = delivery_service.get_delivery_info("kaggle-002", admin)

        assert result.order_id == "kaggle-002"
        assert result.is_historical is True

    def test_kaggle_delivery_data_has_correct_delay(self, delivery_service):
        admin = make_admin()

        result = delivery_service.get_delivery_info("kaggle-002", admin)

        # kaggle-002 has a 5.0 minute delay
        assert result.delivery_delay == 5.0

# test cases for unknown order IDs, ensuring that 404 is returned for both system and Kaggle orders when the ID does not exist, and that the service does not leak information about which type of order was queried

class TestOrderNotFound:

    def test_unknown_order_id_returns_404(self, delivery_service):
        admin = make_admin()

        with pytest.raises(HTTPException) as exc:
            delivery_service.get_delivery_info("does-not-exist", admin)
        assert exc.value.status_code == 404

    def test_unknown_uuid_returns_404(self, delivery_service):
        admin = make_admin()
        fake_id = str(uuid.uuid4())

        with pytest.raises(HTTPException) as exc:
            delivery_service.get_delivery_info(fake_id, admin)
        assert exc.value.status_code == 404


# test cases to confirm that the DeliveryService does not have any methods for creating, updating, or deleting delivery records, ensuring that it is strictly read-only and that all data modifications must go through the OrderRepository or Kaggle CSV

class TestDeliveryReadOnly:

    def test_delivery_service_has_no_update_method(self):
        svc = DeliveryService(order_repo=MagicMock(), kaggle_repo=MagicMock())
        assert not hasattr(svc, "update_delivery")

    def test_delivery_service_has_no_delete_method(self):
        svc = DeliveryService(order_repo=MagicMock(), kaggle_repo=MagicMock())
        assert not hasattr(svc, "delete_delivery")

    def test_delivery_service_has_no_create_method(self):
        svc = DeliveryService(order_repo=MagicMock(), kaggle_repo=MagicMock())
        assert not hasattr(svc, "create_delivery")
