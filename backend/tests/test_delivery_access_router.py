import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

from app.dependencies import ALGORITHM, SECRET_KEY, get_user_repo
from app.main import app
from app.repositories.order_repository import KaggleOrderRepository, OrderRepository
from app.repositories.user_repository import UserRepository
from app.routers import delivery as delivery_router_module
from app.schemas.order import (
    DeliveryMethod,
    Order,
    OrderStatus,
    TrafficCondition,
    WeatherCondition,
)
from app.schemas.user import UserInDB
from app.services.delivery_service import DeliveryService


def make_customer_token(user_id: str) -> str:
    return jwt.encode({"sub": user_id, "role": "customer"}, SECRET_KEY, algorithm=ALGORITHM)


def make_owner_token(restaurant_id: int, user_id: str) -> str:
    return jwt.encode(
        {"sub": user_id, "role": "owner", "restaurant_id": restaurant_id},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def make_admin_token(user_id: str) -> str:
    return jwt.encode({"sub": user_id, "role": "admin"}, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def temp_users_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([], f)
        return Path(f.name)


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
def client(temp_users_file, order_repo, kaggle_repo):
    user_repo = UserRepository(temp_users_file)
    svc = DeliveryService(order_repo=order_repo, kaggle_repo=kaggle_repo)

    app.dependency_overrides[get_user_repo] = lambda: user_repo
    delivery_router_module.delivery_service = svc

    with TestClient(app) as c:
        yield c, order_repo, user_repo

    app.dependency_overrides.clear()
    delivery_router_module.delivery_service = DeliveryService()


def add_user(user_repo: UserRepository, role: str, restaurant_id: int = None) -> UserInDB:
    user = UserInDB(
        id=uuid.uuid4(),
        email=f"{role}-{uuid.uuid4()}@test.com",
        role=role,
        password_hash="hashed",
        restaurant_id=restaurant_id,
    )
    user_repo.create_user(user)
    return user


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


class TestListDeliveryAuth:

    def test_no_token_returns_401(self, client):
        c, _, _ = client
        resp = c.get("/delivery")
        assert resp.status_code == 401

    def test_bad_token_returns_401(self, client):
        c, _, _ = client
        resp = c.get("/delivery", headers={"Authorization": "Bearer bad-token"})
        assert resp.status_code == 401


class TestCustomerListDelivery:

    def test_customer_gets_own_orders_only(self, client):
        c, order_repo, user_repo = client
        customer = add_user(user_repo, "customer")
        other_id = str(uuid.uuid4())
        own_order = insert_order(order_repo, str(customer.id))
        insert_order(order_repo, other_id)
        token = make_customer_token(str(customer.id))

        resp = c.get("/delivery", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["order_id"] == str(own_order.order_id)

    def test_customer_gets_empty_list_with_no_orders(self, client):
        c, _, user_repo = client
        customer = add_user(user_repo, "customer")
        token = make_customer_token(str(customer.id))

        resp = c.get("/delivery", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        assert resp.json() == []

    def test_customer_response_has_correct_shape(self, client):
        c, order_repo, user_repo = client
        customer = add_user(user_repo, "customer")
        insert_order(order_repo, str(customer.id))
        token = make_customer_token(str(customer.id))

        resp = c.get("/delivery", headers={"Authorization": f"Bearer {token}"})

        data = resp.json()[0]
        assert "order_id" in data
        assert "delivery_distance" in data
        assert "is_historical" in data
        assert data["is_historical"] is False

    def test_customer_sees_no_kaggle_records(self, client):
        c, order_repo, user_repo = client
        customer = add_user(user_repo, "customer")
        insert_order(order_repo, str(customer.id))
        token = make_customer_token(str(customer.id))

        resp = c.get("/delivery", headers={"Authorization": f"Bearer {token}"})

        assert all(r["is_historical"] is False for r in resp.json())


class TestOwnerListDelivery:

    def test_owner_gets_restaurant_system_orders(self, client):
        c, order_repo, user_repo = client
        owner = add_user(user_repo, "owner", restaurant_id=16)
        insert_order(order_repo, str(uuid.uuid4()), restaurant_id=16)
        insert_order(order_repo, str(uuid.uuid4()), restaurant_id=30)
        token = make_owner_token(16, str(owner.id))

        resp = c.get("/delivery", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        system_orders = [r for r in resp.json() if not r["is_historical"]]
        assert len(system_orders) == 1

    def test_owner_gets_restaurant_kaggle_orders(self, client):
        c, _, user_repo = client
        owner = add_user(user_repo, "owner", restaurant_id=16)
        token = make_owner_token(16, str(owner.id))

        resp = c.get("/delivery", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        kaggle_orders = [r for r in resp.json() if r["is_historical"]]
        assert len(kaggle_orders) == 1
        assert kaggle_orders[0]["order_id"] == "kaggle-001"

    def test_owner_does_not_see_other_restaurant_orders(self, client):
        c, order_repo, user_repo = client
        owner = add_user(user_repo, "owner", restaurant_id=16)
        insert_order(order_repo, str(uuid.uuid4()), restaurant_id=30)
        token = make_owner_token(16, str(owner.id))

        resp = c.get("/delivery", headers={"Authorization": f"Bearer {token}"})

        system_orders = [r for r in resp.json() if not r["is_historical"]]
        assert len(system_orders) == 0

    def test_owner_gets_empty_list_for_no_matching_orders(self, client):
        c, order_repo, user_repo = client
        owner = add_user(user_repo, "owner", restaurant_id=99)
        insert_order(order_repo, str(uuid.uuid4()), restaurant_id=16)
        token = make_owner_token(99, str(owner.id))

        resp = c.get("/delivery", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        assert resp.json() == []


class TestAdminListDelivery:

    def test_admin_gets_all_system_orders(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        insert_order(order_repo, str(uuid.uuid4()), restaurant_id=16)
        insert_order(order_repo, str(uuid.uuid4()), restaurant_id=30)
        token = make_admin_token(str(admin.id))

        resp = c.get("/delivery", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        system_orders = [r for r in resp.json() if not r["is_historical"]]
        assert len(system_orders) == 2

    def test_admin_gets_all_kaggle_orders(self, client):
        c, _, user_repo = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        resp = c.get("/delivery", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        kaggle_orders = [r for r in resp.json() if r["is_historical"]]
        assert len(kaggle_orders) == 2

    def test_admin_sees_both_system_and_kaggle(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        insert_order(order_repo, str(uuid.uuid4()))
        token = make_admin_token(str(admin.id))

        resp = c.get("/delivery", headers={"Authorization": f"Bearer {token}"})

        data = resp.json()
        assert any(r["is_historical"] is False for r in data)
        assert any(r["is_historical"] is True for r in data)

    def test_admin_gets_empty_list_when_no_orders(self, temp_users_file):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            empty_orders = Path(f.name)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(
                "order_id,restaurant_id,customer_id,food_item,"
                "order_value,order_time,delivery_distance,"
                "delivery_time_actual,delivery_delay\n"
            )
            empty_csv = Path(f.name)

        user_repo = UserRepository(temp_users_file)
        svc = DeliveryService(
            order_repo=OrderRepository(orders_path=empty_orders),
            kaggle_repo=KaggleOrderRepository(csv_path=empty_csv),
        )
        app.dependency_overrides[get_user_repo] = lambda: user_repo
        delivery_router_module.delivery_service = svc

        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        with TestClient(app) as c:
            resp = c.get("/delivery", headers={"Authorization": f"Bearer {token}"})

        app.dependency_overrides.clear()
        delivery_router_module.delivery_service = DeliveryService()

        assert resp.status_code == 200
        assert resp.json() == []
