# Integration tests for the delivery router (GET /delivery/{order_id})
import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

from app.dependencies import ALGORITHM, SECRET_KEY, get_current_user, get_user_repo
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


# --- Token helpers ---

def make_customer_token(user_id: str = None) -> str:
    uid = user_id or str(uuid.uuid4())
    return jwt.encode(
        {"sub": uid, "role": "customer"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def make_owner_token(restaurant_id: int, user_id: str = None) -> str:
    uid = user_id or str(uuid.uuid4())
    return jwt.encode(
        {"sub": uid, "role": "owner", "restaurant_id": restaurant_id},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def make_admin_token(user_id: str = None) -> str:
    uid = user_id or str(uuid.uuid4())
    return jwt.encode(
        {"sub": uid, "role": "admin"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# --- Fixtures ---

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


# Full test client with overridden delivery service and user repo
@pytest.fixture
def client(temp_users_file, order_repo, kaggle_repo):
    user_repo = UserRepository(temp_users_file)
    svc = DeliveryService(order_repo=order_repo, kaggle_repo=kaggle_repo)

    app.dependency_overrides[get_user_repo] = lambda: user_repo

    # save the real user in user_repo so get_current_user can look them up
    # (we register users below per test; for now the user_repo is empty)
    app.dependency_overrides[get_user_repo] = lambda: user_repo

    # override delivery service on the router module
    delivery_router_module.delivery_service = svc

    with TestClient(app) as c:
        yield c, order_repo, user_repo, svc

    app.dependency_overrides.clear()
    # reset router service back to default
    delivery_router_module.delivery_service = DeliveryService()


# helper to add a user to the repo and return their UUID
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


# helper to insert a system order directly
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


# --- Auth tests ---

class TestDeliveryAuth:

    def test_no_token_returns_401(self, client):
        c, _, _, _ = client
        resp = c.get("/delivery/some-order-id")
        assert resp.status_code == 401

    def test_bad_token_returns_401(self, client):
        c, _, _, _ = client
        resp = c.get(
            "/delivery/some-order-id",
            headers={"Authorization": "Bearer this-is-not-a-valid-token"},
        )
        assert resp.status_code == 401


# --- Customer access to system orders ---

class TestCustomerDeliveryAccess:

    def test_customer_gets_own_order(self, client):
        c, order_repo, user_repo, _ = client
        user = add_user(user_repo, "customer")
        order = insert_order(order_repo, str(user.id), restaurant_id=16)
        token = make_customer_token(str(user.id))

        resp = c.get(
            f"/delivery/{order.order_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["order_id"] == str(order.order_id)
        assert data["delivery_distance"] == 5.0
        assert data["delivery_method"] == "Bike"
        assert data["traffic_condition"] == "Low"
        assert data["weather_condition"] == "Sunny"
        assert data["is_historical"] is False

    def test_customer_blocked_from_other_customer_order(self, client):
        c, order_repo, user_repo, _ = client
        owner_user = add_user(user_repo, "customer")
        other_user = add_user(user_repo, "customer")
        order = insert_order(order_repo, str(owner_user.id))
        token = make_customer_token(str(other_user.id))

        resp = c.get(
            f"/delivery/{order.order_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 403

    def test_customer_blocked_from_kaggle_order(self, client):
        c, _, user_repo, _ = client
        user = add_user(user_repo, "customer")
        token = make_customer_token(str(user.id))

        resp = c.get(
            "/delivery/kaggle-001",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 403

    def test_customer_404_for_unknown_order(self, client):
        c, _, user_repo, _ = client
        user = add_user(user_repo, "customer")
        token = make_customer_token(str(user.id))
        fake_id = str(uuid.uuid4())

        resp = c.get(
            f"/delivery/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 404


# --- Owner access ---

class TestOwnerDeliveryAccess:

    def test_owner_gets_own_restaurant_system_order(self, client):
        c, order_repo, user_repo, _ = client
        owner = add_user(user_repo, "owner", restaurant_id=16)
        customer = add_user(user_repo, "customer")
        order = insert_order(order_repo, str(customer.id), restaurant_id=16)
        token = make_owner_token(16, str(owner.id))

        resp = c.get(
            f"/delivery/{order.order_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        assert resp.json()["order_id"] == str(order.order_id)

    def test_owner_blocked_from_different_restaurant_order(self, client):
        c, order_repo, user_repo, _ = client
        owner = add_user(user_repo, "owner", restaurant_id=16)
        customer = add_user(user_repo, "customer")
        order = insert_order(order_repo, str(customer.id), restaurant_id=30)
        token = make_owner_token(16, str(owner.id))

        resp = c.get(
            f"/delivery/{order.order_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 403

    def test_owner_gets_kaggle_order_for_their_restaurant(self, client):
        c, _, user_repo, _ = client
        owner = add_user(user_repo, "owner", restaurant_id=16)
        token = make_owner_token(16, str(owner.id))

        resp = c.get(
            "/delivery/kaggle-001",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["order_id"] == "kaggle-001"
        assert data["delivery_time"] == 30.0
        assert data["delivery_delay"] == 0.0
        assert data["is_historical"] is True

    def test_owner_blocked_from_kaggle_order_of_other_restaurant(self, client):
        c, _, user_repo, _ = client
        owner = add_user(user_repo, "owner", restaurant_id=16)
        token = make_owner_token(16, str(owner.id))

        # kaggle-002 belongs to restaurant 30
        resp = c.get(
            "/delivery/kaggle-002",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 403


# --- Admin access ---

class TestAdminDeliveryAccess:

    def test_admin_gets_any_system_order(self, client):
        c, order_repo, user_repo, _ = client
        admin = add_user(user_repo, "admin")
        customer = add_user(user_repo, "customer")
        order = insert_order(order_repo, str(customer.id), restaurant_id=30)
        token = make_admin_token(str(admin.id))

        resp = c.get(
            f"/delivery/{order.order_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200

    def test_admin_gets_kaggle_order(self, client):
        c, _, user_repo, _ = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        resp = c.get(
            "/delivery/kaggle-002",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["order_id"] == "kaggle-002"
        assert data["is_historical"] is True

    def test_admin_404_for_unknown_order(self, client):
        c, _, user_repo, _ = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))
        fake_id = str(uuid.uuid4())

        resp = c.get(
            f"/delivery/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 404


# --- No write endpoints exist ---

class TestDeliveryReadOnlyEndpoints:

    def test_put_delivery_not_allowed(self, client):
        c, _, user_repo, _ = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        resp = c.put(
            "/delivery/kaggle-001",
            headers={"Authorization": f"Bearer {token}"},
            json={"delivery_distance": 9.9},
        )
        # 405 Method Not Allowed since PUT is not registered
        assert resp.status_code == 405

    def test_post_delivery_not_allowed(self, client):
        c, _, user_repo, _ = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        resp = c.post(
            "/delivery/kaggle-001",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert resp.status_code == 405

    def test_delete_delivery_not_allowed(self, client):
        c, _, user_repo, _ = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        resp = c.delete(
            "/delivery/kaggle-001",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 405

    def test_patch_delivery_not_allowed(self, client):
        c, _, user_repo, _ = client
        admin = add_user(user_repo, "admin")
        token = make_admin_token(str(admin.id))

        resp = c.patch(
            "/delivery/kaggle-001",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
        assert resp.status_code == 405
