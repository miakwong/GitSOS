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


def make_customer_token(user_id: str = None) -> str:
    uid = user_id or str(uuid.uuid4())
    return jwt.encode({"sub": uid, "role": "customer"}, SECRET_KEY, algorithm=ALGORITHM)


def make_owner_token(restaurant_id: int, user_id: str = None) -> str:
    uid = user_id or str(uuid.uuid4())
    return jwt.encode(
        {"sub": uid, "role": "owner", "restaurant_id": restaurant_id},
        SECRET_KEY, algorithm=ALGORITHM,
    )


def make_admin_token(user_id: str = None) -> str:
    uid = user_id or str(uuid.uuid4())
    return jwt.encode({"sub": uid, "role": "admin"}, SECRET_KEY, algorithm=ALGORITHM)


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


def insert_order(order_repo: OrderRepository, restaurant_id: int = 16) -> Order:
    order = Order(
        order_id=uuid.uuid4(),
        customer_id=str(uuid.uuid4()),
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


def set_delivered(order_repo: OrderRepository, order_id: str):
    order_repo.update_order_status(order_id, OrderStatus.DELIVERED)


VALID_OUTCOME = {"actual_delivery_time": 30.0, "delivery_delay": 2.0}


class TestOutcomeAuth:

    def test_no_token_returns_401(self, client):
        c, order_repo, _ = client
        order = insert_order(order_repo)
        resp = c.patch(f"/delivery/{order.order_id}/outcome", json=VALID_OUTCOME)
        assert resp.status_code == 401

    def test_bad_token_returns_401(self, client):
        c, order_repo, _ = client
        order = insert_order(order_repo)
        resp = c.patch(
            f"/delivery/{order.order_id}/outcome",
            headers={"Authorization": "Bearer bad-token"},
            json=VALID_OUTCOME,
        )
        assert resp.status_code == 401


class TestOwnerRecordsOutcome:

    def test_owner_records_outcome_for_delivered_order(self, client):
        c, order_repo, user_repo = client
        owner = add_user(user_repo, "owner", restaurant_id=16)
        order = insert_order(order_repo, restaurant_id=16)
        set_delivered(order_repo, str(order.order_id))
        token = make_owner_token(16, str(owner.id))

        resp = c.patch(
            f"/delivery/{order.order_id}/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json=VALID_OUTCOME,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["actual_delivery_time"] == 30.0
        assert data["delivery_delay"] == 2.0

    def test_owner_blocked_from_other_restaurant_order(self, client):
        c, order_repo, user_repo = client
        owner = add_user(user_repo, "owner", restaurant_id=16)
        order = insert_order(order_repo, restaurant_id=30)
        set_delivered(order_repo, str(order.order_id))
        token = make_owner_token(16, str(owner.id))

        resp = c.patch(
            f"/delivery/{order.order_id}/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json=VALID_OUTCOME,
        )

        assert resp.status_code == 403

    def test_owner_rejected_for_non_delivered_order(self, client):
        c, order_repo, user_repo = client
        owner = add_user(user_repo, "owner", restaurant_id=16)
        order = insert_order(order_repo, restaurant_id=16)
        token = make_owner_token(16, str(owner.id))

        resp = c.patch(
            f"/delivery/{order.order_id}/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json=VALID_OUTCOME,
        )

        assert resp.status_code == 400


class TestAdminRecordsOutcome:

    def test_admin_records_outcome_for_any_delivered_order(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        order = insert_order(order_repo, restaurant_id=30)
        set_delivered(order_repo, str(order.order_id))
        token = make_admin_token(str(admin.id))

        resp = c.patch(
            f"/delivery/{order.order_id}/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json=VALID_OUTCOME,
        )

        assert resp.status_code == 200

    def test_admin_rejected_for_non_delivered_order(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        order = insert_order(order_repo)
        order_repo.update_order_status(str(order.order_id), OrderStatus.PREPARING)
        token = make_admin_token(str(admin.id))

        resp = c.patch(
            f"/delivery/{order.order_id}/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json=VALID_OUTCOME,
        )

        assert resp.status_code == 400

    def test_admin_rejected_for_kaggle_order(self, client):
        c, _, user_repo = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        resp = c.patch(
            "/delivery/kaggle-001/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json=VALID_OUTCOME,
        )

        assert resp.status_code == 400
        assert "Kaggle" in resp.json()["detail"]

    def test_admin_404_for_unknown_order(self, client):
        c, _, user_repo = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        resp = c.patch(
            f"/delivery/{uuid.uuid4()}/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json=VALID_OUTCOME,
        )

        assert resp.status_code == 404


class TestCustomerCannotRecordOutcome:

    def test_customer_blocked_from_recording_outcome(self, client):
        c, order_repo, user_repo = client
        customer = add_user(user_repo, "customer")
        order = insert_order(order_repo)
        set_delivered(order_repo, str(order.order_id))
        token = make_customer_token(str(customer.id))

        resp = c.patch(
            f"/delivery/{order.order_id}/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json=VALID_OUTCOME,
        )

        assert resp.status_code == 403


class TestOutcomeImmutability:

    def test_second_record_attempt_rejected(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        order = insert_order(order_repo)
        set_delivered(order_repo, str(order.order_id))
        token = make_admin_token(str(admin.id))

        c.patch(
            f"/delivery/{order.order_id}/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json=VALID_OUTCOME,
        )
        resp = c.patch(
            f"/delivery/{order.order_id}/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json={"actual_delivery_time": 99.0, "delivery_delay": 99.0},
        )

        assert resp.status_code == 400
        assert "already been recorded" in resp.json()["detail"]

    def test_delivery_params_unchanged_after_outcome(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        order = insert_order(order_repo)
        set_delivered(order_repo, str(order.order_id))
        token = make_admin_token(str(admin.id))

        resp = c.patch(
            f"/delivery/{order.order_id}/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json=VALID_OUTCOME,
        )

        data = resp.json()
        assert data["delivery_distance"] == 5.0
        assert data["delivery_method"] == "Bike"
        assert data["traffic_condition"] == "Low"
        assert data["weather_condition"] == "Sunny"


class TestOutcomePayloadValidation:

    def test_missing_actual_delivery_time_returns_422(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        order = insert_order(order_repo)
        set_delivered(order_repo, str(order.order_id))
        token = make_admin_token(str(admin.id))

        resp = c.patch(
            f"/delivery/{order.order_id}/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json={"delivery_delay": 2.0},
        )

        assert resp.status_code == 422

    def test_actual_delivery_time_zero_returns_422(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        order = insert_order(order_repo)
        set_delivered(order_repo, str(order.order_id))
        token = make_admin_token(str(admin.id))

        resp = c.patch(
            f"/delivery/{order.order_id}/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json={"actual_delivery_time": 0.0, "delivery_delay": 0.0},
        )

        assert resp.status_code == 422

    def test_missing_delivery_delay_returns_422(self, client):
        c, order_repo, user_repo = client
        admin = add_user(user_repo, "admin")
        order = insert_order(order_repo)
        set_delivered(order_repo, str(order.order_id))
        token = make_admin_token(str(admin.id))

        resp = c.patch(
            f"/delivery/{order.order_id}/outcome",
            headers={"Authorization": f"Bearer {token}"},
            json={"actual_delivery_time": 30.0},
        )

        assert resp.status_code == 422
