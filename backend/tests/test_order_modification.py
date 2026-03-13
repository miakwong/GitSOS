# Tests for order modification and cancellation functionality
import json
import tempfile
from pathlib import Path

import pytest
from app.main import app
from app.repositories.order_repository import KaggleOrderRepository, OrderRepository
from app.schemas.order import (
    DeliveryMethod,
    OrderCreate,
    OrderStatus,
    OrderUpdate,
    TrafficCondition,
    WeatherCondition,
)
from app.services.order_service import OrderService
from fastapi import HTTPException
from fastapi.testclient import TestClient

client = TestClient(app)


# --- Fixtures ---


# Create a temporary JSON file for system orders
@pytest.fixture
def temp_orders_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([], f)
        return Path(f.name)


# Create a temporary CSV file with sample Kaggle data
@pytest.fixture
def temp_kaggle_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("order_id,restaurant_id,food_item,customer_id,order_value\n")
        f.write("kaggle-001,16,Taccos,cust-123,25.50\n")
        f.write("kaggle-002,16,Burritos,cust-123,18.00\n")
        f.write("kaggle-003,30,Pasta,cust-456,22.00\n")
        return Path(f.name)


# Order repository with temp file
@pytest.fixture
def order_repo(temp_orders_file):
    return OrderRepository(orders_path=temp_orders_file)


# Kaggle repository with temp CSV
@pytest.fixture
def kaggle_repo(temp_kaggle_csv):
    return KaggleOrderRepository(csv_path=temp_kaggle_csv)


# Order service with test repositories
@pytest.fixture
def order_service(order_repo, kaggle_repo):
    return OrderService(order_repo=order_repo, kaggle_repo=kaggle_repo)


# Create a sample order for testing modifications
@pytest.fixture
def sample_order(order_service):
    order_data = OrderCreate(
        customer_id="cust-123",
        restaurant_id=16,
        food_item="Taccos",
        order_value=25.50,
        delivery_distance=5.0,
        delivery_method=DeliveryMethod.BIKE,
    )
    return order_service.create_order(order_data)


# --- OrderUpdate Schema Validation Tests ---


class TestOrderUpdateSchemaValidation:

    # Test valid partial update schema
    def test_valid_partial_update(self):
        update = OrderUpdate(food_item="Burritos")
        assert update.food_item == "Burritos"
        assert update.delivery_method is None
        assert update.traffic_condition is None

    # Test all fields update schema
    def test_valid_full_update(self):
        update = OrderUpdate(
            food_item="Burritos",
            order_value=30.00,
            delivery_distance=7.5,
            delivery_method=DeliveryMethod.CAR,
            traffic_condition=TrafficCondition.HIGH,
            weather_condition=WeatherCondition.RAINY,
        )
        assert update.food_item == "Burritos"
        assert update.order_value == 30.00
        assert update.delivery_distance == 7.5
        assert update.delivery_method == DeliveryMethod.CAR
        assert update.traffic_condition == TrafficCondition.HIGH
        assert update.weather_condition == WeatherCondition.RAINY

    # Test empty update schema (no fields)
    def test_empty_update_allowed(self):
        update = OrderUpdate()
        assert update.food_item is None
        assert update.order_value is None

    # Test empty food_item string rejected
    def test_empty_food_item_rejected(self):
        with pytest.raises(ValueError):
            OrderUpdate(food_item="")

    # Test whitespace-only food_item rejected
    def test_whitespace_food_item_rejected(self):
        with pytest.raises(ValueError):
            OrderUpdate(food_item="   ")

    # Test delivery_distance below minimum rejected
    def test_delivery_distance_below_minimum_rejected(self):
        with pytest.raises(ValueError):
            OrderUpdate(delivery_distance=1.9)

    # Test delivery_distance above maximum rejected
    def test_delivery_distance_above_maximum_rejected(self):
        with pytest.raises(ValueError):
            OrderUpdate(delivery_distance=15.1)

    # Test invalid delivery_method rejected
    def test_invalid_delivery_method_rejected(self):
        with pytest.raises(ValueError):
            OrderUpdate(delivery_method="Helicopter")


# --- Service Tests: Ownership Validation ---


class TestOrderOwnershipValidation:

    # Test customer can update their own order
    def test_owner_can_update_own_order(self, order_service, sample_order):
        update_data = OrderUpdate(traffic_condition=TrafficCondition.MEDIUM)
        updated_order = order_service.update_order(
            str(sample_order.order_id), "cust-123", update_data  # Same as order owner
        )
        assert updated_order.traffic_condition == TrafficCondition.MEDIUM

    # Test customer cannot update another customer's order
    def test_non_owner_cannot_update_order(self, order_service, sample_order):
        update_data = OrderUpdate(traffic_condition=TrafficCondition.HIGH)
        with pytest.raises(HTTPException) as exc_info:
            order_service.update_order(
                str(sample_order.order_id),
                "cust-456",  # Different customer
                update_data,
            )
        assert exc_info.value.status_code == 403
        assert "own orders" in exc_info.value.detail

    # Test customer can cancel their own order
    def test_owner_can_cancel_own_order(self, order_service, sample_order):
        cancelled_order = order_service.cancel_order(
            str(sample_order.order_id), "cust-123"  # Same as order owner
        )
        assert cancelled_order.order_status == OrderStatus.CANCELLED

    # Test customer cannot cancel another customer's order
    def test_non_owner_cannot_cancel_order(self, order_service, sample_order):
        with pytest.raises(HTTPException) as exc_info:
            order_service.cancel_order(
                str(sample_order.order_id), "cust-456"  # Different customer
            )
        assert exc_info.value.status_code == 403
        assert "own orders" in exc_info.value.detail


# --- Service Tests: Workflow Status Validation ---


class TestOrderWorkflowValidation:

    # Test order in Placed status can be updated
    def test_placed_order_can_be_updated(self, order_service, sample_order):
        assert sample_order.order_status == OrderStatus.PLACED
        update_data = OrderUpdate(weather_condition=WeatherCondition.RAINY)
        updated_order = order_service.update_order(
            str(sample_order.order_id), "cust-123", update_data
        )
        assert updated_order.weather_condition == WeatherCondition.RAINY

    # Test order in Placed status can be cancelled
    def test_placed_order_can_be_cancelled(self, order_service, sample_order):
        assert sample_order.order_status == OrderStatus.PLACED
        cancelled_order = order_service.cancel_order(
            str(sample_order.order_id), "cust-123"
        )
        assert cancelled_order.order_status == OrderStatus.CANCELLED

    # Test order in Paid status cannot be updated (not in MODIFIABLE_STATUSES)
    def test_paid_order_cannot_be_updated(
        self, order_service, sample_order, order_repo
    ):
        # Manually change status to Paid
        order_repo.update_order_status(str(sample_order.order_id), OrderStatus.PAID)

        update_data = OrderUpdate(traffic_condition=TrafficCondition.HIGH)
        with pytest.raises(HTTPException) as exc_info:
            order_service.update_order(
                str(sample_order.order_id), "cust-123", update_data
            )
        assert exc_info.value.status_code == 400
        assert "cannot be modified" in exc_info.value.detail

    # Test order in Paid status can be cancelled (in CANCELLABLE_STATUSES)
    def test_paid_order_can_be_cancelled(self, order_service, sample_order, order_repo):
        # Manually change status to Paid
        order_repo.update_order_status(str(sample_order.order_id), OrderStatus.PAID)

        cancelled_order = order_service.cancel_order(
            str(sample_order.order_id), "cust-123"
        )
        assert cancelled_order.order_status == OrderStatus.CANCELLED

    # Test order in Preparing status cannot be updated
    def test_preparing_order_cannot_be_updated(
        self, order_service, sample_order, order_repo
    ):
        order_repo.update_order_status(
            str(sample_order.order_id), OrderStatus.PREPARING
        )

        update_data = OrderUpdate(food_item="Burritos")
        with pytest.raises(HTTPException) as exc_info:
            order_service.update_order(
                str(sample_order.order_id), "cust-123", update_data
            )
        assert exc_info.value.status_code == 400

    # Test order in Preparing status cannot be cancelled
    def test_preparing_order_cannot_be_cancelled(
        self, order_service, sample_order, order_repo
    ):
        order_repo.update_order_status(
            str(sample_order.order_id), OrderStatus.PREPARING
        )

        with pytest.raises(HTTPException) as exc_info:
            order_service.cancel_order(str(sample_order.order_id), "cust-123")
        assert exc_info.value.status_code == 400
        assert "cannot be cancelled" in exc_info.value.detail

    # Test order in Delivered status cannot be updated
    def test_delivered_order_cannot_be_updated(
        self, order_service, sample_order, order_repo
    ):
        order_repo.update_order_status(
            str(sample_order.order_id), OrderStatus.DELIVERED
        )

        update_data = OrderUpdate(delivery_method=DeliveryMethod.CAR)
        with pytest.raises(HTTPException) as exc_info:
            order_service.update_order(
                str(sample_order.order_id), "cust-123", update_data
            )
        assert exc_info.value.status_code == 400

    # Test order in Delivered status cannot be cancelled
    def test_delivered_order_cannot_be_cancelled(
        self, order_service, sample_order, order_repo
    ):
        order_repo.update_order_status(
            str(sample_order.order_id), OrderStatus.DELIVERED
        )

        with pytest.raises(HTTPException) as exc_info:
            order_service.cancel_order(str(sample_order.order_id), "cust-123")
        assert exc_info.value.status_code == 400

    # Test already cancelled order cannot be updated
    def test_cancelled_order_cannot_be_updated(
        self, order_service, sample_order, order_repo
    ):
        order_repo.update_order_status(
            str(sample_order.order_id), OrderStatus.CANCELLED
        )

        update_data = OrderUpdate(traffic_condition=TrafficCondition.LOW)
        with pytest.raises(HTTPException) as exc_info:
            order_service.update_order(
                str(sample_order.order_id), "cust-123", update_data
            )
        assert exc_info.value.status_code == 400

    # Test already cancelled order cannot be cancelled again
    def test_cancelled_order_cannot_be_cancelled_again(
        self, order_service, sample_order, order_repo
    ):
        order_repo.update_order_status(
            str(sample_order.order_id), OrderStatus.CANCELLED
        )

        with pytest.raises(HTTPException) as exc_info:
            order_service.cancel_order(str(sample_order.order_id), "cust-123")
        assert exc_info.value.status_code == 400


# --- Service Tests: Food Item Validation ---


class TestFoodItemValidation:

    # Test updating food_item to valid item from same restaurant
    def test_update_food_item_valid(self, order_service, sample_order):
        update_data = OrderUpdate(food_item="Burritos")  # Valid for restaurant 16
        updated_order = order_service.update_order(
            str(sample_order.order_id), "cust-123", update_data
        )
        assert updated_order.food_item == "Burritos"

    # Test updating food_item to invalid item (not from restaurant)
    def test_update_food_item_invalid_for_restaurant(self, order_service, sample_order):
        update_data = OrderUpdate(food_item="Pasta")  # Only at restaurant 30, not 16
        with pytest.raises(HTTPException) as exc_info:
            order_service.update_order(
                str(sample_order.order_id), "cust-123", update_data
            )
        assert exc_info.value.status_code == 400
        assert "not offered" in exc_info.value.detail

    # Test updating food_item to completely unknown item
    def test_update_food_item_nonexistent(self, order_service, sample_order):
        update_data = OrderUpdate(food_item="Sushi")  # Doesn't exist anywhere
        with pytest.raises(HTTPException) as exc_info:
            order_service.update_order(
                str(sample_order.order_id), "cust-123", update_data
            )
        assert exc_info.value.status_code == 400
        assert "not offered" in exc_info.value.detail


# --- Service Tests: Kaggle Order Rejection ---


class TestKaggleOrderRejection:

    # Test Kaggle historical orders cannot be updated
    def test_kaggle_order_cannot_be_updated(self, order_service):
        update_data = OrderUpdate(traffic_condition=TrafficCondition.HIGH)
        with pytest.raises(HTTPException) as exc_info:
            order_service.update_order("kaggle-001", "cust-123", update_data)
        assert exc_info.value.status_code == 400
        assert "Kaggle" in exc_info.value.detail
        assert "cannot be modified" in exc_info.value.detail

    # Test Kaggle historical orders cannot be cancelled
    def test_kaggle_order_cannot_be_cancelled(self, order_service):
        with pytest.raises(HTTPException) as exc_info:
            order_service.cancel_order("kaggle-001", "cust-123")
        assert exc_info.value.status_code == 400
        assert "Kaggle" in exc_info.value.detail
        assert "cannot be cancelled" in exc_info.value.detail


# --- Service Tests: Non-Existent Order Handling ---


class TestNonExistentOrderHandling:

    # Test updating non-existent order returns 404
    def test_update_nonexistent_order(self, order_service):
        update_data = OrderUpdate(traffic_condition=TrafficCondition.HIGH)
        with pytest.raises(HTTPException) as exc_info:
            order_service.update_order("non-existent-id", "cust-123", update_data)
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    # Test cancelling non-existent order returns 404
    def test_cancel_nonexistent_order(self, order_service):
        with pytest.raises(HTTPException) as exc_info:
            order_service.cancel_order("non-existent-id", "cust-123")
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail


# --- Repository Tests: Update Operations ---


class TestOrderRepositoryUpdate:

    # Test update_order applies partial updates
    def test_update_order_partial(self, order_repo):
        # Create an order first
        order_data = OrderCreate(
            customer_id="cust-123",
            restaurant_id=16,
            food_item="Taccos",
            order_value=25.50,
            delivery_distance=5.0,
            delivery_method=DeliveryMethod.BIKE,
        )
        created_order = order_repo.create_order(order_data)

        # Update only traffic_condition
        update_data = OrderUpdate(traffic_condition=TrafficCondition.HIGH)
        updated_order = order_repo.update_order(
            str(created_order.order_id), update_data
        )

        assert updated_order.traffic_condition == TrafficCondition.HIGH
        assert updated_order.food_item == "Taccos"  # Unchanged
        assert updated_order.delivery_method == DeliveryMethod.BIKE  # Unchanged

    # Test update_order applies all fields
    def test_update_order_full(self, order_repo):
        order_data = OrderCreate(
            customer_id="cust-123",
            restaurant_id=16,
            food_item="Taccos",
            order_value=25.50,
            delivery_distance=5.0,
            delivery_method=DeliveryMethod.BIKE,
        )
        created_order = order_repo.create_order(order_data)

        update_data = OrderUpdate(
            food_item="Burritos",
            order_value=30.00,
            delivery_distance=8.0,
            delivery_method=DeliveryMethod.CAR,
            traffic_condition=TrafficCondition.HIGH,
            weather_condition=WeatherCondition.RAINY,
        )
        updated_order = order_repo.update_order(
            str(created_order.order_id), update_data
        )

        assert updated_order.food_item == "Burritos"
        assert updated_order.order_value == 30.00
        assert updated_order.delivery_distance == 8.0
        assert updated_order.delivery_method == DeliveryMethod.CAR
        assert updated_order.traffic_condition == TrafficCondition.HIGH
        assert updated_order.weather_condition == WeatherCondition.RAINY

    # Test update_order_status changes status
    def test_update_order_status(self, order_repo):
        order_data = OrderCreate(
            customer_id="cust-123",
            restaurant_id=16,
            food_item="Taccos",
            order_value=25.50,
            delivery_distance=5.0,
            delivery_method=DeliveryMethod.BIKE,
        )
        created_order = order_repo.create_order(order_data)
        assert created_order.order_status == OrderStatus.PLACED

        updated_order = order_repo.update_order_status(
            str(created_order.order_id), OrderStatus.CANCELLED
        )
        assert updated_order.order_status == OrderStatus.CANCELLED

    # Test update nonexistent order returns None
    def test_update_nonexistent_order_returns_none(self, order_repo):
        update_data = OrderUpdate(traffic_condition=TrafficCondition.HIGH)
        result = order_repo.update_order("non-existent-id", update_data)
        assert result is None

    # Test update_order_status for nonexistent order returns None
    def test_update_status_nonexistent_order_returns_none(self, order_repo):
        result = order_repo.update_order_status(
            "non-existent-id", OrderStatus.CANCELLED
        )
        assert result is None


# --- API Endpoint Tests ---


class TestOrderModificationEndpoints:

    # Test PUT endpoint with valid update
    def test_put_order_valid_update(self, order_service, sample_order, monkeypatch):
        # Monkeypatch the order_service in the router
        from app.routers import orders as orders_router

        monkeypatch.setattr(orders_router, "order_service", order_service)

        response = client.put(
            f"/orders/{sample_order.order_id}",
            params={"customer_id": "cust-123"},
            json={"traffic_condition": "High"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["traffic_condition"] == "High"

    # Test PUT endpoint with ownership violation
    def test_put_order_ownership_violation(
        self, order_service, sample_order, monkeypatch
    ):
        from app.routers import orders as orders_router

        monkeypatch.setattr(orders_router, "order_service", order_service)

        response = client.put(
            f"/orders/{sample_order.order_id}",
            params={"customer_id": "cust-456"},  # Wrong customer
            json={"traffic_condition": "High"},
        )
        assert response.status_code == 403

    # Test DELETE/cancel endpoint with valid request
    def test_cancel_order_valid(self, order_service, sample_order, monkeypatch):
        from app.routers import orders as orders_router

        monkeypatch.setattr(orders_router, "order_service", order_service)

        response = client.delete(
            f"/orders/{sample_order.order_id}/cancel",
            params={"customer_id": "cust-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["order_status"] == "Cancelled"

    # Test DELETE/cancel endpoint with ownership violation
    def test_cancel_order_ownership_violation(
        self, order_service, sample_order, monkeypatch
    ):
        from app.routers import orders as orders_router

        monkeypatch.setattr(orders_router, "order_service", order_service)

        response = client.delete(
            f"/orders/{sample_order.order_id}/cancel",
            params={"customer_id": "cust-456"},  # Wrong customer
        )
        assert response.status_code == 403
