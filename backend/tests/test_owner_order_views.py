import json
import tempfile
from pathlib import Path
from uuid import uuid4

import jwt
import pytest
from app.dependencies import ALGORITHM, SECRET_KEY
from app.main import app
from app.repositories.order_repository import KaggleOrderRepository, OrderRepository
from app.repositories.user_repository import UserRepository
from app.schemas.order import DeliveryMethod, OrderCreate
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.services.order_service import OrderService
from fastapi import HTTPException
from fastapi.testclient import TestClient

client = TestClient(app)


def make_owner_token(rest_id: int) -> str:
    return jwt.encode(
        {"sub": str(uuid4()), "role": "owner", "restaurant_id": rest_id},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def make_customer_token() -> str:
    return jwt.encode(
        {"sub": str(uuid4()), "role": "customer"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


@pytest.fixture
def temp_orders_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([], f)
        return Path(f.name)


@pytest.fixture
def temp_kaggle_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("order_id,restaurant_id,food_item,customer_id,order_value\n")
        f.write("kaggle-001,16,Taccos,cust-123,25.50\n")
        f.write("kaggle-002,16,Burritos,cust-123,18.00\n")
        f.write("kaggle-003,30,Pasta,cust-456,22.00\n")
        return Path(f.name)


@pytest.fixture
def order_repo(temp_orders_file):
    return OrderRepository(orders_path=temp_orders_file)


@pytest.fixture
def kaggle_repo(temp_kaggle_csv):
    return KaggleOrderRepository(csv_path=temp_kaggle_csv)


@pytest.fixture
def order_service(order_repo, kaggle_repo):
    return OrderService(order_repo=order_repo, kaggle_repo=kaggle_repo)


@pytest.fixture
def r16_order(order_service):
    return order_service.create_order(
        OrderCreate(
            customer_id="cust-123",
            restaurant_id=16,
            food_item="Taccos",
            order_value=25.50,
            delivery_distance=5.0,
            delivery_method=DeliveryMethod.BIKE,
        )
    )


@pytest.fixture
def r30_order(order_service):
    return order_service.create_order(
        OrderCreate(
            customer_id="cust-456",
            restaurant_id=30,
            food_item="Pasta",
            order_value=22.00,
            delivery_distance=7.0,
            delivery_method=DeliveryMethod.CAR,
        )
    )


class TestUserSchemaOwner:

    def test_owner_needs_restaurant_id(self):
        with pytest.raises(ValueError, match="restaurant_id is required"):
            UserCreate(email="owner@example.com", password="pass", role="owner")

    def test_owner_valid(self):
        user = UserCreate(
            email="owner@example.com", password="pass", role="owner", restaurant_id=16
        )
        assert user.restaurant_id == 16

    def test_customer_cant_have_restaurant_id(self):
        with pytest.raises(ValueError):
            UserCreate(
                email="c@example.com",
                password="pass",
                role="customer",
                restaurant_id=16,
            )

    def test_customer_no_restaurant_id_ok(self):
        user = UserCreate(email="c@example.com", password="pass", role="customer")
        assert user.restaurant_id is None


class TestOwnerTokenAuth:

    @pytest.fixture
    def auth_service(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            tmp = Path(f.name)
        return AuthService(
            user_repo=UserRepository(tmp), secret_key=SECRET_KEY, algorithm=ALGORITHM
        )

    def test_owner_token_has_restaurant_id(self, auth_service):
        token = auth_service.create_access_token(
            user_id=uuid4(), role="owner", restaurant_id=16
        )
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["restaurant_id"] == 16

    def test_customer_token_no_restaurant_id(self, auth_service):
        token = auth_service.create_access_token(user_id=uuid4(), role="customer")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "restaurant_id" not in payload

    def test_login_owner_token_carries_restaurant_id(self, auth_service):
        from app.schemas.user import UserLogin

        auth_service.register_user(
            UserCreate(
                email="o@test.com", password="pw", role="owner", restaurant_id=16
            )
        )
        token = auth_service.login_user(UserLogin(email="o@test.com", password="pw"))
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["restaurant_id"] == 16


class TestOwnerOrderService:

    def test_owner_only_sees_own_orders(self, order_service, r16_order, r30_order):
        orders = order_service.get_orders_for_owner(16)
        ids = [str(o.order_id) for o in orders]
        assert str(r16_order.order_id) in ids
        assert str(r30_order.order_id) not in ids

    def test_no_orders_gives_empty_list(self, order_service):
        assert order_service.get_orders_for_owner(999) == []

    def test_get_order_for_owner_ok(self, order_service, r16_order):
        order = order_service.get_order_for_owner(str(r16_order.order_id), 16)
        assert order.restaurant_id == 16

    def test_get_order_wrong_restaurant_is_403(self, order_service, r30_order):
        with pytest.raises(HTTPException) as exc:
            order_service.get_order_for_owner(str(r30_order.order_id), 16)
        assert exc.value.status_code == 403

    def test_get_order_not_found_is_404(self, order_service):
        with pytest.raises(HTTPException) as exc:
            order_service.get_order_for_owner(
                "00000000-0000-0000-0000-000000000000", 16
            )
        assert exc.value.status_code == 404


class TestOwnerRepoFilter:

    def test_filters_by_restaurant(self, order_repo):
        order_repo.create_order(
            OrderCreate(
                customer_id="cust-123",
                restaurant_id=16,
                food_item="Taccos",
                order_value=20.0,
                delivery_distance=5.0,
                delivery_method=DeliveryMethod.BIKE,
            )
        )
        order_repo.create_order(
            OrderCreate(
                customer_id="cust-456",
                restaurant_id=30,
                food_item="Pasta",
                order_value=22.0,
                delivery_distance=7.0,
                delivery_method=DeliveryMethod.CAR,
            )
        )
        result = order_repo.get_orders_by_restaurant_id(16)
        assert len(result) == 1
        assert result[0].restaurant_id == 16

    def test_unknown_restaurant_returns_empty(self, order_repo):
        assert order_repo.get_orders_by_restaurant_id(9999) == []


class TestOwnerEndpoints:

    def test_list_orders_ok(self, order_service, r16_order, monkeypatch):
        from app.routers import orders as orders_router

        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.get(
            "/orders/owner/restaurant",
            headers={"Authorization": f"Bearer {make_owner_token(16)}"},
        )
        assert resp.status_code == 200
        assert any(o["order_id"] == str(r16_order.order_id) for o in resp.json())

    def test_list_orders_excludes_other_restaurant(
        self, order_service, r16_order, r30_order, monkeypatch
    ):
        from app.routers import orders as orders_router

        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.get(
            "/orders/owner/restaurant",
            headers={"Authorization": f"Bearer {make_owner_token(16)}"},
        )
        ids = [o["order_id"] for o in resp.json()]
        assert str(r16_order.order_id) in ids
        assert str(r30_order.order_id) not in ids

    def test_get_single_order_ok(self, order_service, r16_order, monkeypatch):
        from app.routers import orders as orders_router

        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.get(
            f"/orders/owner/restaurant/{r16_order.order_id}",
            headers={"Authorization": f"Bearer {make_owner_token(16)}"},
        )
        assert resp.status_code == 200
        assert resp.json()["order_id"] == str(r16_order.order_id)

    def test_get_order_wrong_restaurant_403(
        self, order_service, r30_order, monkeypatch
    ):
        from app.routers import orders as orders_router

        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.get(
            f"/orders/owner/restaurant/{r30_order.order_id}",
            headers={"Authorization": f"Bearer {make_owner_token(16)}"},
        )
        assert resp.status_code == 403

    def test_no_token_401(self):
        assert client.get("/orders/owner/restaurant").status_code == 401

    def test_bad_token_401(self):
        resp = client.get(
            "/orders/owner/restaurant",
            headers={"Authorization": "Bearer garbage"},
        )
        assert resp.status_code == 401

    def test_customer_token_403(self):
        resp = client.get(
            "/orders/owner/restaurant",
            headers={"Authorization": f"Bearer {make_customer_token()}"},
        )
        assert resp.status_code == 403

    def test_put_not_allowed(self):
        resp = client.put(
            "/orders/owner/restaurant",
            headers={"Authorization": f"Bearer {make_owner_token(16)}"},
            json={},
        )
        assert resp.status_code == 405

    def test_kaggle_order_not_accessible(self, order_service, monkeypatch):
        from app.routers import orders as orders_router

        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.get(
            "/orders/owner/restaurant/kaggle-001",
            headers={"Authorization": f"Bearer {make_owner_token(16)}"},
        )
        assert resp.status_code == 404
