import json
import tempfile
import pytest
from pathlib import Path
from uuid import uuid4

import jwt
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import SECRET_KEY, ALGORITHM
from app.schemas.order import (
    Order, OrderCreate, OrderStatus, OrderStatusUpdate,
    DeliveryMethod, VALID_TRANSITIONS,
)
from app.repositories.order_repository import OrderRepository, KaggleOrderRepository
from app.services.order_service import OrderService

client = TestClient(app)


# helper

def make_owner_token(rest_id: int) -> str:
    return jwt.encode(
        {"sub": str(uuid4()), "role": "owner", "restaurant_id": rest_id},
        SECRET_KEY, algorithm=ALGORITHM,
    )


def make_admin_token() -> str:
    return jwt.encode(
        {"sub": str(uuid4()), "role": "admin"},
        SECRET_KEY, algorithm=ALGORITHM,
    )


def make_customer_token() -> str:
    return jwt.encode(
        {"sub": str(uuid4()), "role": "customer"},
        SECRET_KEY, algorithm=ALGORITHM,
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
    return order_service.create_order(OrderCreate(
        customer_id="cust-123", restaurant_id=16, food_item="Taccos",
        order_value=25.50, delivery_distance=5.0, delivery_method=DeliveryMethod.BIKE,
    ))


@pytest.fixture
def r30_order(order_service):
    return order_service.create_order(OrderCreate(
        customer_id="cust-456", restaurant_id=30, food_item="Pasta",
        order_value=22.00, delivery_distance=7.0, delivery_method=DeliveryMethod.CAR,
    ))


#  Schema tests 

class TestOrderStatusUpdateSchema:

    def test_valid_status_update(self):
        update = OrderStatusUpdate(order_status=OrderStatus.PAID)
        assert update.order_status == OrderStatus.PAID

    def test_all_statuses_accepted(self):
        for s in OrderStatus:
            update = OrderStatusUpdate(order_status=s)
            assert update.order_status == s

    def test_invalid_status_rejected(self):
        with pytest.raises(Exception):
            OrderStatusUpdate(order_status="InvalidStatus")


#  valid transition tests

class TestValidTransitionsStructure:

    def test_all_statuses_have_transition_entry(self):
        for s in OrderStatus:
            assert s in VALID_TRANSITIONS

    def test_placed_can_go_to_paid_or_cancelled(self):
        assert OrderStatus.PAID in VALID_TRANSITIONS[OrderStatus.PLACED]
        assert OrderStatus.CANCELLED in VALID_TRANSITIONS[OrderStatus.PLACED]

    def test_paid_can_go_to_preparing_or_cancelled(self):
        assert OrderStatus.PREPARING in VALID_TRANSITIONS[OrderStatus.PAID]
        assert OrderStatus.CANCELLED in VALID_TRANSITIONS[OrderStatus.PAID]

    def test_preparing_can_go_to_delivered(self):
        assert OrderStatus.DELIVERED in VALID_TRANSITIONS[OrderStatus.PREPARING]
        assert len(VALID_TRANSITIONS[OrderStatus.PREPARING]) == 1

    def test_delivered_is_terminal(self):
        assert len(VALID_TRANSITIONS[OrderStatus.DELIVERED]) == 0

    def test_cancelled_is_terminal(self):
        assert len(VALID_TRANSITIONS[OrderStatus.CANCELLED]) == 0




class TestAdvanceOrderStatusService:

    def test_placed_to_paid(self, order_service, r16_order):
        result = order_service.advance_order_status(
            str(r16_order.order_id), OrderStatus.PAID, 16
        )
        assert result.order_status == OrderStatus.PAID

    def test_placed_to_cancelled(self, order_service, r16_order):
        result = order_service.advance_order_status(
            str(r16_order.order_id), OrderStatus.CANCELLED, 16
        )
        assert result.order_status == OrderStatus.CANCELLED

    def test_paid_to_preparing(self, order_service, r16_order, order_repo):
        order_repo.update_order_status(str(r16_order.order_id), OrderStatus.PAID)
        result = order_service.advance_order_status(
            str(r16_order.order_id), OrderStatus.PREPARING, 16
        )
        assert result.order_status == OrderStatus.PREPARING

    def test_paid_to_cancelled(self, order_service, r16_order, order_repo):
        order_repo.update_order_status(str(r16_order.order_id), OrderStatus.PAID)
        result = order_service.advance_order_status(
            str(r16_order.order_id), OrderStatus.CANCELLED, 16
        )
        assert result.order_status == OrderStatus.CANCELLED

    def test_preparing_to_delivered(self, order_service, r16_order, order_repo):
        order_repo.update_order_status(str(r16_order.order_id), OrderStatus.PREPARING)
        result = order_service.advance_order_status(
            str(r16_order.order_id), OrderStatus.DELIVERED, 16
        )
        assert result.order_status == OrderStatus.DELIVERED

    def test_invalid_transition_placed_to_preparing(self, order_service, r16_order):
        with pytest.raises(HTTPException) as exc:
            order_service.advance_order_status(
                str(r16_order.order_id), OrderStatus.PREPARING, 16
            )
        assert exc.value.status_code == 400
        assert "Cannot transition" in exc.value.detail

    def test_invalid_transition_placed_to_delivered(self, order_service, r16_order):
        with pytest.raises(HTTPException) as exc:
            order_service.advance_order_status(
                str(r16_order.order_id), OrderStatus.DELIVERED, 16
            )
        assert exc.value.status_code == 400

    def test_invalid_transition_paid_to_placed(self, order_service, r16_order, order_repo):
        order_repo.update_order_status(str(r16_order.order_id), OrderStatus.PAID)
        with pytest.raises(HTTPException) as exc:
            order_service.advance_order_status(
                str(r16_order.order_id), OrderStatus.PLACED, 16
            )
        assert exc.value.status_code == 400

    def test_terminal_delivered_cannot_transition(self, order_service, r16_order, order_repo):
        order_repo.update_order_status(str(r16_order.order_id), OrderStatus.DELIVERED)
        with pytest.raises(HTTPException) as exc:
            order_service.advance_order_status(
                str(r16_order.order_id), OrderStatus.CANCELLED, 16
            )
        assert exc.value.status_code == 400
        assert "terminal state" in exc.value.detail

    def test_terminal_cancelled_cannot_transition(self, order_service, r16_order, order_repo):
        order_repo.update_order_status(str(r16_order.order_id), OrderStatus.CANCELLED)
        with pytest.raises(HTTPException) as exc:
            order_service.advance_order_status(
                str(r16_order.order_id), OrderStatus.PLACED, 16
            )
        assert exc.value.status_code == 400
        assert "terminal state" in exc.value.detail

    def test_wrong_restaurant_raises_403(self, order_service, r30_order):
        with pytest.raises(HTTPException) as exc:
            order_service.advance_order_status(
                str(r30_order.order_id), OrderStatus.PAID, 16
            )
        assert exc.value.status_code == 403

    def test_order_not_found_raises_404(self, order_service):
        with pytest.raises(HTTPException) as exc:
            order_service.advance_order_status(
                "00000000-0000-0000-0000-000000000000", OrderStatus.PAID, 16
            )
        assert exc.value.status_code == 404

    def test_kaggle_order_rejected(self, order_service):
        with pytest.raises(HTTPException) as exc:
            order_service.advance_order_status("kaggle-001", OrderStatus.PAID, 16)
        assert exc.value.status_code == 400
        assert "Kaggle" in exc.value.detail


# admin override tests

class TestAdminOverrideStatusService:

    def test_admin_can_set_paid(self, order_service, r16_order):
        result = order_service.admin_override_status(
            str(r16_order.order_id), OrderStatus.PAID
        )
        assert result.order_status == OrderStatus.PAID

    def test_admin_can_set_preparing_directly(self, order_service, r16_order):
        result = order_service.admin_override_status(
            str(r16_order.order_id), OrderStatus.PREPARING
        )
        assert result.order_status == OrderStatus.PREPARING

    def test_admin_can_set_delivered_from_placed(self, order_service, r16_order):
        result = order_service.admin_override_status(
            str(r16_order.order_id), OrderStatus.DELIVERED
        )
        assert result.order_status == OrderStatus.DELIVERED

    def test_admin_can_override_terminal_delivered(self, order_service, r16_order, order_repo):
        order_repo.update_order_status(str(r16_order.order_id), OrderStatus.DELIVERED)
        result = order_service.admin_override_status(
            str(r16_order.order_id), OrderStatus.PLACED
        )
        assert result.order_status == OrderStatus.PLACED

    def test_admin_can_override_terminal_cancelled(self, order_service, r16_order, order_repo):
        order_repo.update_order_status(str(r16_order.order_id), OrderStatus.CANCELLED)
        result = order_service.admin_override_status(
            str(r16_order.order_id), OrderStatus.PAID
        )
        assert result.order_status == OrderStatus.PAID

    def test_admin_kaggle_order_rejected(self, order_service):
        with pytest.raises(HTTPException) as exc:
            order_service.admin_override_status("kaggle-001", OrderStatus.PAID)
        assert exc.value.status_code == 400
        assert "Kaggle" in exc.value.detail

    def test_admin_order_not_found_raises_404(self, order_service):
        with pytest.raises(HTTPException) as exc:
            order_service.admin_override_status(
                "00000000-0000-0000-0000-000000000000", OrderStatus.PAID
            )
        assert exc.value.status_code == 404


# API endpoint tests for owner status updates

class TestOwnerStatusEndpoint:

    def test_owner_advance_placed_to_paid(self, order_service, r16_order, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            f"/orders/owner/restaurant/{r16_order.order_id}/status",
            headers={"Authorization": f"Bearer {make_owner_token(16)}"},
            json={"order_status": "Paid"},
        )
        assert resp.status_code == 200
        assert resp.json()["order_status"] == "Paid"

    def test_owner_advance_placed_to_cancelled(self, order_service, r16_order, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            f"/orders/owner/restaurant/{r16_order.order_id}/status",
            headers={"Authorization": f"Bearer {make_owner_token(16)}"},
            json={"order_status": "Cancelled"},
        )
        assert resp.status_code == 200
        assert resp.json()["order_status"] == "Cancelled"

    def test_owner_invalid_transition_returns_400(self, order_service, r16_order, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            f"/orders/owner/restaurant/{r16_order.order_id}/status",
            headers={"Authorization": f"Bearer {make_owner_token(16)}"},
            json={"order_status": "Delivered"},
        )
        assert resp.status_code == 400

    def test_owner_wrong_restaurant_returns_403(self, order_service, r30_order, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            f"/orders/owner/restaurant/{r30_order.order_id}/status",
            headers={"Authorization": f"Bearer {make_owner_token(16)}"},
            json={"order_status": "Paid"},
        )
        assert resp.status_code == 403

    def test_owner_no_token_returns_401(self, order_service, r16_order, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            f"/orders/owner/restaurant/{r16_order.order_id}/status",
            json={"order_status": "Paid"},
        )
        assert resp.status_code == 401

    def test_customer_token_returns_403(self, order_service, r16_order, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            f"/orders/owner/restaurant/{r16_order.order_id}/status",
            headers={"Authorization": f"Bearer {make_customer_token()}"},
            json={"order_status": "Paid"},
        )
        assert resp.status_code == 403

    def test_admin_token_returns_403_on_owner_endpoint(self, order_service, r16_order, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            f"/orders/owner/restaurant/{r16_order.order_id}/status",
            headers={"Authorization": f"Bearer {make_admin_token()}"},
            json={"order_status": "Paid"},
        )
        assert resp.status_code == 403

    def test_kaggle_order_returns_400(self, order_service, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            "/orders/owner/restaurant/kaggle-001/status",
            headers={"Authorization": f"Bearer {make_owner_token(16)}"},
            json={"order_status": "Paid"},
        )
        assert resp.status_code == 400


# API endpoint tests for admin status overrides

class TestAdminStatusEndpoint:

    def test_admin_can_set_any_status(self, order_service, r16_order, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            f"/orders/admin/{r16_order.order_id}/status",
            headers={"Authorization": f"Bearer {make_admin_token()}"},
            json={"order_status": "Preparing"},
        )
        assert resp.status_code == 200
        assert resp.json()["order_status"] == "Preparing"

    def test_admin_can_override_terminal_state(self, order_service, r16_order, order_repo, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        order_repo.update_order_status(str(r16_order.order_id), OrderStatus.DELIVERED)
        resp = client.patch(
            f"/orders/admin/{r16_order.order_id}/status",
            headers={"Authorization": f"Bearer {make_admin_token()}"},
            json={"order_status": "Placed"},
        )
        assert resp.status_code == 200
        assert resp.json()["order_status"] == "Placed"

    def test_owner_token_returns_403_on_admin_endpoint(self, order_service, r16_order, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            f"/orders/admin/{r16_order.order_id}/status",
            headers={"Authorization": f"Bearer {make_owner_token(16)}"},
            json={"order_status": "Paid"},
        )
        assert resp.status_code == 403

    def test_customer_token_returns_403_on_admin_endpoint(self, order_service, r16_order, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            f"/orders/admin/{r16_order.order_id}/status",
            headers={"Authorization": f"Bearer {make_customer_token()}"},
            json={"order_status": "Paid"},
        )
        assert resp.status_code == 403

    def test_admin_no_token_returns_401(self, order_service, r16_order, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            f"/orders/admin/{r16_order.order_id}/status",
            json={"order_status": "Paid"},
        )
        assert resp.status_code == 401

    def test_admin_kaggle_order_returns_400(self, order_service, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            "/orders/admin/kaggle-001/status",
            headers={"Authorization": f"Bearer {make_admin_token()}"},
            json={"order_status": "Paid"},
        )
        assert resp.status_code == 400

    def test_admin_order_not_found_returns_404(self, order_service, monkeypatch):
        from app.routers import orders as orders_router
        monkeypatch.setattr(orders_router, "order_service", order_service)

        resp = client.patch(
            "/orders/admin/00000000-0000-0000-0000-000000000000/status",
            headers={"Authorization": f"Bearer {make_admin_token()}"},
            json={"order_status": "Paid"},
        )
        assert resp.status_code == 404
