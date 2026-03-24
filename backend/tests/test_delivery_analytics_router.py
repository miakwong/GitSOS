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
from tests.helpers import insert_analytics_order


def make_admin_token(user_id: str) -> str:
    return jwt.encode({"sub": user_id, "role": "admin"}, SECRET_KEY, algorithm=ALGORITHM)


def make_customer_token(user_id: str) -> str:
    return jwt.encode({"sub": user_id, "role": "customer"}, SECRET_KEY, algorithm=ALGORITHM)


def make_owner_token(restaurant_id: int, user_id: str) -> str:
    return jwt.encode(
        {"sub": user_id, "role": "owner", "restaurant_id": restaurant_id},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


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


class TestAnalyticsAuth:

    def test_no_token_returns_401(self, client):
        c, _, _ = client
        resp = c.get("/delivery/analytics")
        assert resp.status_code == 401

    def test_bad_token_returns_401(self, client):
        c, _, _ = client
        resp = c.get("/delivery/analytics", headers={"Authorization": "Bearer bad-token"})
        assert resp.status_code == 401

    def test_customer_returns_403(self, client):
        c, _, user_repo = client
        customer = add_user(user_repo, "customer")
        token = make_customer_token(str(customer.id))

        resp = c.get("/delivery/analytics", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 403

    def test_owner_returns_403(self, client):
        c, _, user_repo = client
        owner = add_user(user_repo, "owner", restaurant_id=16)
        token = make_owner_token(16, str(owner.id))

        resp = c.get("/delivery/analytics", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 403

    def test_admin_gets_200(self, client):
        c, _, user_repo = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        resp = c.get("/delivery/analytics", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200


class TestAnalyticsResponseShape:

    def test_response_has_required_fields(self, client):
        c, _, user_repo = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        resp = c.get("/delivery/analytics", headers={"Authorization": f"Bearer {token}"})

        data = resp.json()
        assert "total_orders" in data
        assert "records" in data
        assert "avg_delivery_time" in data
        assert "avg_delivery_delay" in data

    def test_empty_when_no_orders(self, client):
        c, _, user_repo = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        resp = c.get("/delivery/analytics", headers={"Authorization": f"Bearer {token}"})

        data = resp.json()
        assert data["total_orders"] == 0
        assert data["records"] == []
        assert data["avg_delivery_time"] is None
        assert data["avg_delivery_delay"] is None


class TestAnalyticsFiltering:

    def test_no_filter_returns_all(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        insert_analytics_order(order_repo, traffic=TrafficCondition.LOW)
        insert_analytics_order(order_repo, traffic=TrafficCondition.HIGH)
        token = make_admin_token(str(admin.id))

        resp = c.get("/delivery/analytics", headers={"Authorization": f"Bearer {token}"})

        assert resp.json()["total_orders"] == 2

    def test_filter_by_traffic_condition(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        insert_analytics_order(order_repo, traffic=TrafficCondition.LOW)
        insert_analytics_order(order_repo, traffic=TrafficCondition.HIGH)
        token = make_admin_token(str(admin.id))

        resp = c.get(
            "/delivery/analytics",
            params={"traffic_condition": "Low"},
            headers={"Authorization": f"Bearer {token}"},
        )

        data = resp.json()
        assert data["total_orders"] == 1
        assert data["traffic_condition"] == "Low"

    def test_filter_by_weather_condition(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        insert_analytics_order(order_repo, weather=WeatherCondition.RAINY)
        insert_analytics_order(order_repo, weather=WeatherCondition.SUNNY)
        token = make_admin_token(str(admin.id))

        resp = c.get(
            "/delivery/analytics",
            params={"weather_condition": "Rainy"},
            headers={"Authorization": f"Bearer {token}"},
        )

        data = resp.json()
        assert data["total_orders"] == 1
        assert data["weather_condition"] == "Rainy"

    def test_filter_by_both_conditions(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        insert_analytics_order(order_repo, traffic=TrafficCondition.LOW, weather=WeatherCondition.SUNNY)
        insert_analytics_order(order_repo, traffic=TrafficCondition.LOW, weather=WeatherCondition.RAINY)
        insert_analytics_order(order_repo, traffic=TrafficCondition.HIGH, weather=WeatherCondition.SUNNY)
        token = make_admin_token(str(admin.id))

        resp = c.get(
            "/delivery/analytics",
            params={"traffic_condition": "Low", "weather_condition": "Sunny"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.json()["total_orders"] == 1

    def test_no_match_returns_empty(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        insert_analytics_order(order_repo, traffic=TrafficCondition.LOW)
        token = make_admin_token(str(admin.id))

        resp = c.get(
            "/delivery/analytics",
            params={"traffic_condition": "High"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.json()["total_orders"] == 0

    def test_invalid_traffic_condition_returns_422(self, client):
        c, _, user_repo = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        resp = c.get(
            "/delivery/analytics",
            params={"traffic_condition": "blah"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 422

    def test_invalid_weather_condition_returns_422(self, client):
        c, _, user_repo = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        resp = c.get(
            "/delivery/analytics",
            params={"weather_condition": "blah"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 422


class TestAnalyticsAggregates:

    def test_avg_computed_from_outcomes(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        insert_analytics_order(order_repo, actual_delivery_time=30.0, delivery_delay=5.0)
        insert_analytics_order(order_repo, actual_delivery_time=50.0, delivery_delay=15.0)
        token = make_admin_token(str(admin.id))

        resp = c.get("/delivery/analytics", headers={"Authorization": f"Bearer {token}"})

        data = resp.json()
        assert data["avg_delivery_time"] == 40.0
        assert data["avg_delivery_delay"] == 10.0

    def test_avg_none_when_no_outcomes(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        insert_analytics_order(order_repo)
        token = make_admin_token(str(admin.id))

        resp = c.get("/delivery/analytics", headers={"Authorization": f"Bearer {token}"})

        data = resp.json()
        assert data["avg_delivery_time"] is None
        assert data["avg_delivery_delay"] is None
