import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies import ALGORITHM, SECRET_KEY, get_auth_service, get_order_service, get_user_repo
from app.main import app
from app.repositories.order_repository import OrderRepository
from app.repositories.user_repository import UserRepository
from app.schemas.order import DeliveryMethod, OrderCreate
from app.services.auth_service import TOKEN_BLACKLIST, AuthService
from app.services.order_service import OrderService

@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as temp_dir:
        users_file = Path(temp_dir) / "users.json"
        orders_file = Path(temp_dir) / "orders.json"
        orders_file.write_text("[]")

        user_repo = UserRepository(users_file)
        auth_service = AuthService(
            user_repo=user_repo,
            secret_key=SECRET_KEY,
            algorithm=ALGORITHM,
        )
        order_repo = OrderRepository(orders_path=orders_file)
        order_service = _make_order_service(order_repo)

        TOKEN_BLACKLIST.clear()

        app.dependency_overrides[get_auth_service] = lambda: auth_service
        app.dependency_overrides[get_user_repo] = lambda: user_repo
        app.dependency_overrides[get_order_service] = lambda: order_service

        with TestClient(app) as c:
            yield c, order_repo

        app.dependency_overrides.clear()
        TOKEN_BLACKLIST.clear()


def _make_order_service(order_repo: OrderRepository) -> OrderService:
    return OrderService(order_repo=order_repo, kaggle_repo=MagicMock())



# helpers 
def _register(c, email, password="pass1234", role="customer", restaurant_id=None):
    payload = {"email": email, "password": password, "role": role}
    if role == "owner":
        payload["restaurant_id"] = restaurant_id or 1
    return c.post("/auth/register", json=payload)


def _login(c, email, password="pass1234"):
    r = c.post("/auth/login", data={"username": email, "password": password})
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _add_order(order_repo: OrderRepository, customer_id: str) -> str:
    from app.schemas.order import Order, OrderStatus, TrafficCondition, WeatherCondition
    import uuid
    from datetime import datetime, timezone

    order = Order(
        order_id=uuid.uuid4(),
        customer_id=customer_id,
        restaurant_id=1,
        food_item="Burger",
        order_time=datetime.now(timezone.utc),
        order_value=15.0,
        delivery_distance=5.0,
        delivery_method=DeliveryMethod.BIKE,
        traffic_condition=TrafficCondition.LOW,
        weather_condition=WeatherCondition.SUNNY,
        order_status=OrderStatus.PLACED,
    )
    orders = order_repo._load_orders()
    orders.append(order.model_dump(mode="json"))
    order_repo._save_orders(orders)
    return str(order.order_id)

# tests 

def test_unauthenticated_profile_returns_401(client):
    c, _ = client
    r = c.get("/auth/profile")
    assert r.status_code == 401


def test_customer_can_get_own_profile(client):
    c, _ = client
    _register(c, "cust@test.com", role="customer")
    token = _login(c, "cust@test.com")

    r = c.get("/auth/profile", headers=_headers(token))

    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "cust@test.com"
    assert data["role"] == "customer"
    assert "id" in data


def test_owner_can_get_own_profile(client):
    c, _ = client
    _register(c, "owner@test.com", role="owner", restaurant_id=5)
    token = _login(c, "owner@test.com")

    r = c.get("/auth/profile", headers=_headers(token))

    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "owner@test.com"
    assert data["role"] == "owner"
    assert data["restaurant_id"] == 5


def test_admin_can_get_own_profile(client):
    c, _ = client
    _register(c, "admin@test.com", role="admin")
    token = _login(c, "admin@test.com")

    r = c.get("/auth/profile", headers=_headers(token))

    assert r.status_code == 200
    assert r.json()["role"] == "admin"


def test_profile_data_belongs_to_requesting_user(client):
    c, _ = client
    _register(c, "alice@test.com", role="customer")
    _register(c, "bob@test.com", role="customer")

    token_alice = _login(c, "alice@test.com")
    token_bob = _login(c, "bob@test.com")

    r_alice = c.get("/auth/profile", headers=_headers(token_alice))
    r_bob = c.get("/auth/profile", headers=_headers(token_bob))

    assert r_alice.json()["email"] == "alice@test.com"
    assert r_bob.json()["email"] == "bob@test.com"
    assert r_alice.json()["id"] != r_bob.json()["id"]


def test_customer_profile_includes_order_count(client):
    c, order_repo = client
    _register(c, "cust@test.com", role="customer")
    token = _login(c, "cust@test.com")

    user_id = c.get("/auth/profile", headers=_headers(token)).json()["id"]
    _add_order(order_repo, user_id)
    _add_order(order_repo, user_id)

    r = c.get("/auth/profile", headers=_headers(token))

    assert r.status_code == 200
    assert r.json()["order_count"] == 2


def test_customer_profile_includes_order_history(client):
    c, order_repo = client
    _register(c, "cust@test.com", role="customer")
    token = _login(c, "cust@test.com")

    user_id = c.get("/auth/profile", headers=_headers(token)).json()["id"]
    order_id = _add_order(order_repo, user_id)

    r = c.get("/auth/profile", headers=_headers(token))

    assert r.json()["order_count"] == 1
    assert order_id in r.json()["order_history"]


def test_customer_order_history_only_contains_own_orders(client):
    c, order_repo = client
    _register(c, "alice@test.com", role="customer")
    _register(c, "bob@test.com", role="customer")

    token_alice = _login(c, "alice@test.com")
    token_bob = _login(c, "bob@test.com")

    alice_id = c.get("/auth/profile", headers=_headers(token_alice)).json()["id"]
    bob_id = c.get("/auth/profile", headers=_headers(token_bob)).json()["id"]

    alice_order = _add_order(order_repo, alice_id)
    _add_order(order_repo, bob_id)

    r = c.get("/auth/profile", headers=_headers(token_alice))

    assert r.json()["order_count"] == 1
    assert alice_order in r.json()["order_history"]


def test_customer_no_orders_shows_zero_count(client):
    c, _ = client
    _register(c, "cust@test.com", role="customer")
    token = _login(c, "cust@test.com")

    r = c.get("/auth/profile", headers=_headers(token))

    assert r.json()["order_count"] == 0
    assert r.json()["order_history"] == []


def test_owner_profile_has_no_order_fields(client):
    c, _ = client
    _register(c, "owner@test.com", role="owner", restaurant_id=10)
    token = _login(c, "owner@test.com")

    r = c.get("/auth/profile", headers=_headers(token))
    data = r.json()

    assert data["restaurant_id"] == 10
    assert data["order_count"] is None
    assert data["order_history"] is None


def test_profile_does_not_expose_password(client):
    c, _ = client
    _register(c, "cust@test.com", role="customer")
    token = _login(c, "cust@test.com")

    r = c.get("/auth/profile", headers=_headers(token))

    assert "password" not in r.json()
    assert "password_hash" not in r.json()


# tests

def test_user_can_get_own_profile_by_id(client):
    c, _ = client
    _register(c, "cust@test.com", role="customer")
    token = _login(c, "cust@test.com")

    user_id = c.get("/auth/profile", headers=_headers(token)).json()["id"]
    r = c.get(f"/auth/users/{user_id}/profile", headers=_headers(token))

    assert r.status_code == 200
    assert r.json()["email"] == "cust@test.com"


def test_cross_user_profile_access_returns_403(client):
    c, _ = client
    _register(c, "alice@test.com", role="customer")
    _register(c, "bob@test.com", role="customer")

    token_alice = _login(c, "alice@test.com")
    token_bob = _login(c, "bob@test.com")

    bob_id = c.get("/auth/profile", headers=_headers(token_bob)).json()["id"]

    r = c.get(f"/auth/users/{bob_id}/profile", headers=_headers(token_alice))

    assert r.status_code == 403


def test_unauthenticated_user_id_profile_returns_401(client):
    c, _ = client
    fake_id = str(uuid4())
    r = c.get(f"/auth/users/{fake_id}/profile")
    assert r.status_code == 401


def test_owner_cannot_access_customer_profile(client):
    c, _ = client
    _register(c, "owner@test.com", role="owner", restaurant_id=1)
    _register(c, "cust@test.com", role="customer")

    token_owner = _login(c, "owner@test.com")
    token_cust = _login(c, "cust@test.com")

    cust_id = c.get("/auth/profile", headers=_headers(token_cust)).json()["id"]

    r = c.get(f"/auth/users/{cust_id}/profile", headers=_headers(token_owner))

    assert r.status_code == 403


def test_owner_profile_by_id_includes_restaurant_id(client):
    c, _ = client
    _register(c, "owner@test.com", role="owner", restaurant_id=7)
    token = _login(c, "owner@test.com")

    owner_id = c.get("/auth/profile", headers=_headers(token)).json()["id"]
    r = c.get(f"/auth/users/{owner_id}/profile", headers=_headers(token))

    assert r.status_code == 200
    assert r.json()["restaurant_id"] == 7


def test_admin_can_view_another_users_profile(client):
    c, _ = client
    _register(c, "admin@test.com", role="admin")
    _register(c, "cust@test.com", role="customer")

    token_admin = _login(c, "admin@test.com")
    token_cust = _login(c, "cust@test.com")

    cust_id = c.get("/auth/profile", headers=_headers(token_cust)).json()["id"]
    r = c.get(f"/auth/users/{cust_id}/profile", headers=_headers(token_admin))

    assert r.status_code == 200
    assert r.json()["email"] == "cust@test.com"


def test_admin_view_nonexistent_user_returns_404(client):
    c, _ = client
    _register(c, "admin@test.com", role="admin")
    token_admin = _login(c, "admin@test.com")

    fake_id = str(uuid4())
    r = c.get(f"/auth/users/{fake_id}/profile", headers=_headers(token_admin))

    assert r.status_code == 404
