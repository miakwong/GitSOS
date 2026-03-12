# Tests for order creation functionality
import pytest
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.order import (
    OrderCreate, Order, OrderStatus,
    DeliveryMethod, TrafficCondition, WeatherCondition
)
from app.repositories.order_repository import OrderRepository, KaggleOrderRepository
from app.services.order_service import OrderService

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


# --- Schema Validation Tests ---

# Tests for OrderCreate schema validation
class TestOrderSchemaValidation:

    # Test valid order creation schema
    def test_valid_order_create(self):
        order = OrderCreate(
            customer_id="cust-123",
            restaurant_id=16,
            food_item="Taccos",
            order_value=25.50,
            delivery_distance=5.0,
            delivery_method=DeliveryMethod.BIKE,
        )
        assert order.customer_id == "cust-123"
        assert order.traffic_condition == TrafficCondition.LOW  # default
        assert order.weather_condition == WeatherCondition.SUNNY  # default

    # Test delivery_distance at minimum boundary (2.0 km)
    def test_delivery_distance_minimum_boundary(self):
        order = OrderCreate(
            customer_id="cust-123",
            restaurant_id=16,
            food_item="Taccos",
            order_value=25.50,
            delivery_distance=2.0,
            delivery_method=DeliveryMethod.WALK,
        )
        assert order.delivery_distance == 2.0

    # Test delivery_distance at maximum boundary (15.0 km)
    def test_delivery_distance_maximum_boundary(self):
        order = OrderCreate(
            customer_id="cust-123",
            restaurant_id=16,
            food_item="Taccos",
            order_value=25.50,
            delivery_distance=15.0,
            delivery_method=DeliveryMethod.CAR,
        )
        assert order.delivery_distance == 15.0

    # Test delivery_distance below minimum is rejected
    def test_delivery_distance_below_minimum_rejected(self):
        with pytest.raises(ValueError):
            OrderCreate(
                customer_id="cust-123",
                restaurant_id=16,
                food_item="Taccos",
                order_value=25.50,
                delivery_distance=1.9,
                delivery_method=DeliveryMethod.WALK,
            )

    # Test delivery_distance above maximum is rejected
    def test_delivery_distance_above_maximum_rejected(self):
        with pytest.raises(ValueError):
            OrderCreate(
                customer_id="cust-123",
                restaurant_id=16,
                food_item="Taccos",
                order_value=25.50,
                delivery_distance=15.1,
                delivery_method=DeliveryMethod.CAR,
            )

    # Test empty food_item is rejected
    def test_empty_food_item_rejected(self):
        with pytest.raises(ValueError):
            OrderCreate(
                customer_id="cust-123",
                restaurant_id=16,
                food_item="",
                order_value=25.50,
                delivery_distance=5.0,
                delivery_method=DeliveryMethod.BIKE,
            )

    # Test whitespace-only food_item is rejected
    def test_whitespace_food_item_rejected(self):
        with pytest.raises(ValueError):
            OrderCreate(
                customer_id="cust-123",
                restaurant_id=16,
                food_item="   ",
                order_value=25.50,
                delivery_distance=5.0,
                delivery_method=DeliveryMethod.BIKE,
            )

    # Test invalid delivery_method is rejected
    def test_invalid_delivery_method_rejected(self):
        with pytest.raises(ValueError):
            OrderCreate(
                customer_id="cust-123",
                restaurant_id=16,
                food_item="Taccos",
                order_value=25.50,
                delivery_distance=5.0,
                delivery_method="Helicopter",
            )

    # Test invalid traffic_condition is rejected
    def test_invalid_traffic_condition_rejected(self):
        with pytest.raises(ValueError):
            OrderCreate(
                customer_id="cust-123",
                restaurant_id=16,
                food_item="Taccos",
                order_value=25.50,
                delivery_distance=5.0,
                delivery_method=DeliveryMethod.BIKE,
                traffic_condition="Extreme",
            )

    # Test invalid weather_condition is rejected
    def test_invalid_weather_condition_rejected(self):
        with pytest.raises(ValueError):
            OrderCreate(
                customer_id="cust-123",
                restaurant_id=16,
                food_item="Taccos",
                order_value=25.50,
                delivery_distance=5.0,
                delivery_method=DeliveryMethod.BIKE,
                weather_condition="Stormy",
            )


# --- Repository Tests ---

# Tests for Kaggle repository (read-only)
class TestKaggleOrderRepository:

    # Test getting unique restaurant IDs
    def test_get_restaurants(self, kaggle_repo):
        restaurants = kaggle_repo.get_restaurants()
        assert 16 in restaurants
        assert 30 in restaurants
        assert len(restaurants) == 2

    # Test getting unique customer IDs
    def test_get_customers(self, kaggle_repo):
        customers = kaggle_repo.get_customers()
        assert "cust-123" in customers
        assert "cust-456" in customers
        assert len(customers) == 2

    # Test getting food items for a specific restaurant
    def test_get_food_items_by_restaurant(self, kaggle_repo):
        food_items = kaggle_repo.get_food_items_by_restaurant(16)
        assert "Taccos" in food_items
        assert "Burritos" in food_items
        assert "Pasta" not in food_items


# Tests for system order repository
class TestOrderRepository:

    # Test creating and persisting an order
    def test_create_order(self, order_repo):
        order_data = OrderCreate(
            customer_id="cust-123",
            restaurant_id=16,
            food_item="Taccos",
            order_value=25.50,
            delivery_distance=5.0,
            delivery_method=DeliveryMethod.BIKE,
        )
        order = order_repo.create_order(order_data)

        assert order.order_id is not None
        assert order.order_status == OrderStatus.PLACED
        assert order.customer_id == "cust-123"

    # Test retrieving all orders
    def test_get_all_orders(self, order_repo):
        # Create two orders
        for _ in range(2):
            order_data = OrderCreate(
                customer_id="cust-123",
                restaurant_id=16,
                food_item="Taccos",
                order_value=25.50,
                delivery_distance=5.0,
                delivery_method=DeliveryMethod.BIKE,
            )
            order_repo.create_order(order_data)

        orders = order_repo.get_all_orders()
        assert len(orders) == 2


# --- Service Tests ---

# Tests for order service business logic
class TestOrderService:

    # Test successful order creation with valid data
    def test_create_order_success(self, order_service):
        order_data = OrderCreate(
            customer_id="cust-123",
            restaurant_id=16,
            food_item="Taccos",
            order_value=25.50,
            delivery_distance=5.0,
            delivery_method=DeliveryMethod.BIKE,
        )
        order = order_service.create_order(order_data)

        assert order.order_id is not None
        assert order.order_status == OrderStatus.PLACED
        assert order.traffic_condition == TrafficCondition.LOW
        assert order.weather_condition == WeatherCondition.SUNNY

    # Test order creation with non-existent customer
    def test_create_order_invalid_customer(self, order_service):
        order_data = OrderCreate(
            customer_id="non-existent",
            restaurant_id=16,
            food_item="Taccos",
            order_value=25.50,
            delivery_distance=5.0,
            delivery_method=DeliveryMethod.BIKE,
        )
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            order_service.create_order(order_data)
        assert exc_info.value.status_code == 400
        assert "Customer" in exc_info.value.detail

    # Test order creation with non-existent restaurant
    def test_create_order_invalid_restaurant(self, order_service):
        order_data = OrderCreate(
            customer_id="cust-123",
            restaurant_id=9999,
            food_item="Taccos",
            order_value=25.50,
            delivery_distance=5.0,
            delivery_method=DeliveryMethod.BIKE,
        )
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            order_service.create_order(order_data)
        assert exc_info.value.status_code == 400
        assert "Restaurant" in exc_info.value.detail

    # Test order creation with food item not offered by restaurant
    def test_create_order_invalid_food_item(self, order_service):
        order_data = OrderCreate(
            customer_id="cust-123",
            restaurant_id=16,
            food_item="Sushi",  # Not offered by restaurant 16
            order_value=25.50,
            delivery_distance=5.0,
            delivery_method=DeliveryMethod.BIKE,
        )
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            order_service.create_order(order_data)
        assert exc_info.value.status_code == 400
        assert "Food item" in exc_info.value.detail

    # Test order creation with custom traffic condition
    def test_order_with_custom_traffic_condition(self, order_service):
        order_data = OrderCreate(
            customer_id="cust-123",
            restaurant_id=16,
            food_item="Taccos",
            order_value=25.50,
            delivery_distance=5.0,
            delivery_method=DeliveryMethod.BIKE,
            traffic_condition=TrafficCondition.HIGH,
        )
        order = order_service.create_order(order_data)
        assert order.traffic_condition == TrafficCondition.HIGH

    # Test order creation with custom weather condition
    def test_order_with_custom_weather_condition(self, order_service):
        order_data = OrderCreate(
            customer_id="cust-123",
            restaurant_id=16,
            food_item="Taccos",
            order_value=25.50,
            delivery_distance=5.0,
            delivery_method=DeliveryMethod.BIKE,
            weather_condition=WeatherCondition.RAINY,
        )
        order = order_service.create_order(order_data)
        assert order.weather_condition == WeatherCondition.RAINY


# --- Enum Tests ---

# Tests for enum value constraints
class TestEnumValues:

    # Test all valid OrderStatus values
    def test_order_status_values(self):
        assert OrderStatus.PLACED.value == "Placed"
        assert OrderStatus.PAID.value == "Paid"
        assert OrderStatus.PREPARING.value == "Preparing"
        assert OrderStatus.DELIVERED.value == "Delivered"
        assert OrderStatus.CANCELLED.value == "Cancelled"

    # Test all valid DeliveryMethod values
    def test_delivery_method_values(self):
        assert DeliveryMethod.WALK.value == "Walk"
        assert DeliveryMethod.BIKE.value == "Bike"
        assert DeliveryMethod.CAR.value == "Car"

    # Test all valid TrafficCondition values
    def test_traffic_condition_values(self):
        assert TrafficCondition.LOW.value == "Low"
        assert TrafficCondition.MEDIUM.value == "Medium"
        assert TrafficCondition.HIGH.value == "High"

    # Test all valid WeatherCondition values
    def test_weather_condition_values(self):
        assert WeatherCondition.SUNNY.value == "Sunny"
        assert WeatherCondition.RAINY.value == "Rainy"
        assert WeatherCondition.SNOWY.value == "Snowy"


# --- Integration Tests ---

# Integration tests for order API endpoints
class TestOrderAPIIntegration:

    # Test POST /orders with missing required field returns 422
    def test_create_order_endpoint_missing_required_field(self):
        response = client.post(
            "/orders/",
            json={
                "customer_id": "cust-123",
                "restaurant_id": 16,
                # missing food_item, delivery_distance, delivery_method
            },
        )
        assert response.status_code == 422

    # Test POST /orders with invalid delivery_distance returns 422
    def test_create_order_endpoint_invalid_delivery_distance(self):
        response = client.post(
            "/orders/",
            json={
                "customer_id": "cust-123",
                "restaurant_id": 16,
                "food_item": "Taccos",
                "order_value": 25.50,
                "delivery_distance": 1.0,  # Below minimum
                "delivery_method": "Bike",
            },
        )
        assert response.status_code == 422

    # Test POST /orders with invalid enum value returns 422
    def test_create_order_endpoint_invalid_enum(self):
        response = client.post(
            "/orders/",
            json={
                "customer_id": "cust-123",
                "restaurant_id": 16,
                "food_item": "Taccos",
                "order_value": 25.50,
                "delivery_distance": 5.0,
                "delivery_method": "Helicopter",  # Invalid
            },
        )
        assert response.status_code == 422
