import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.repositories.order_repository import KaggleOrderRepository, OrderRepository
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


def make_admin() -> UserInDB:
    return UserInDB(
        id=uuid.uuid4(),
        email="admin@test.com",
        role="admin",
        password_hash="hashed",
    )


def make_customer() -> UserInDB:
    return UserInDB(
        id=uuid.uuid4(),
        email="cust@test.com",
        role="customer",
        password_hash="hashed",
    )


def make_owner() -> UserInDB:
    return UserInDB(
        id=uuid.uuid4(),
        email="owner@test.com",
        role="owner",
        password_hash="hashed",
        restaurant_id=16,
    )


@pytest.fixture
def temp_orders_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([], f)
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture
def temp_kaggle_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(
            "order_id,restaurant_id,customer_id,food_item,"
            "order_value,order_time,delivery_distance,"
            "delivery_time_actual,delivery_delay\n"
        )
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture
def order_repo(temp_orders_file):
    return OrderRepository(orders_path=temp_orders_file)


@pytest.fixture
def kaggle_repo(temp_kaggle_csv):
    return KaggleOrderRepository(csv_path=temp_kaggle_csv)


@pytest.fixture
def delivery_service(order_repo, kaggle_repo):
    return DeliveryService(order_repo=order_repo, kaggle_repo=kaggle_repo)


class TestAnalyticsAccessControl:

    def test_customer_gets_403(self, delivery_service):
        customer = make_customer()
        with pytest.raises(Exception) as exc_info:
            delivery_service.get_delivery_analytics(customer)
        assert exc_info.value.status_code == 403

    def test_owner_gets_403(self, delivery_service):
        owner = make_owner()
        with pytest.raises(Exception) as exc_info:
            delivery_service.get_delivery_analytics(owner)
        assert exc_info.value.status_code == 403

    def test_admin_can_access(self, delivery_service):
        admin = make_admin()
        result = delivery_service.get_delivery_analytics(admin)
        assert result is not None


class TestAnalyticsFiltering:

    def test_no_filter_returns_all_orders(self, delivery_service, order_repo):
        admin = make_admin()
        insert_analytics_order(order_repo, traffic=TrafficCondition.LOW)
        insert_analytics_order(order_repo, traffic=TrafficCondition.HIGH)

        result = delivery_service.get_delivery_analytics(admin)

        assert result.total_orders == 2

    def test_filter_by_traffic_condition(self, delivery_service, order_repo):
        admin = make_admin()
        insert_analytics_order(order_repo, traffic=TrafficCondition.LOW)
        insert_analytics_order(order_repo, traffic=TrafficCondition.HIGH)

        result = delivery_service.get_delivery_analytics(admin, traffic_condition="Low")

        assert result.total_orders == 1

    def test_filter_by_weather_condition(self, delivery_service, order_repo):
        admin = make_admin()
        insert_analytics_order(order_repo, weather=WeatherCondition.SUNNY)
        insert_analytics_order(order_repo, weather=WeatherCondition.RAINY)

        result = delivery_service.get_delivery_analytics(admin, weather_condition="Sunny")

        assert result.total_orders == 1

    def test_filter_by_both_conditions(self, delivery_service, order_repo):
        admin = make_admin()
        insert_analytics_order(order_repo, traffic=TrafficCondition.LOW, weather=WeatherCondition.SUNNY)
        insert_analytics_order(order_repo, traffic=TrafficCondition.LOW, weather=WeatherCondition.RAINY)
        insert_analytics_order(order_repo, traffic=TrafficCondition.HIGH, weather=WeatherCondition.SUNNY)

        result = delivery_service.get_delivery_analytics(
            admin, traffic_condition="Low", weather_condition="Sunny"
        )

        assert result.total_orders == 1

    def test_no_match_returns_empty(self, delivery_service, order_repo):
        admin = make_admin()
        insert_analytics_order(order_repo, traffic=TrafficCondition.LOW)

        result = delivery_service.get_delivery_analytics(admin, traffic_condition="High")

        assert result.total_orders == 0

    def test_empty_store_returns_empty(self, delivery_service):
        admin = make_admin()

        result = delivery_service.get_delivery_analytics(admin)

        assert result.total_orders == 0

    def test_invalid_traffic_condition_raises_422(self, delivery_service):
        admin = make_admin()
        with pytest.raises(Exception) as exc_info:
            delivery_service.get_delivery_analytics(admin, traffic_condition="blah")
        assert exc_info.value.status_code == 422

    def test_invalid_weather_condition_raises_422(self, delivery_service):
        admin = make_admin()
        with pytest.raises(Exception) as exc_info:
            delivery_service.get_delivery_analytics(admin, weather_condition="blah")
        assert exc_info.value.status_code == 422


class TestAnalyticsAggregates:

    def test_avg_delivery_time_computed_correctly(self, delivery_service, order_repo):
        admin = make_admin()
        insert_analytics_order(order_repo, actual_delivery_time=30.0, delivery_delay=5.0)
        insert_analytics_order(order_repo, actual_delivery_time=50.0, delivery_delay=10.0)

        result = delivery_service.get_delivery_analytics(admin)

        assert result.avg_delivery_time == 40.0
        assert result.avg_delivery_delay == 7.5

    def test_avg_is_none_when_no_outcomes_recorded(self, delivery_service, order_repo):
        admin = make_admin()
        insert_analytics_order(order_repo)

        result = delivery_service.get_delivery_analytics(admin)

        assert result.avg_delivery_time is None
        assert result.avg_delivery_delay is None

    def test_avg_only_uses_orders_with_outcomes(self, delivery_service, order_repo):
        admin = make_admin()
        insert_analytics_order(order_repo, actual_delivery_time=40.0, delivery_delay=0.0)
        insert_analytics_order(order_repo)

        result = delivery_service.get_delivery_analytics(admin)

        assert result.total_orders == 2
        assert result.avg_delivery_time == 40.0

    def test_response_contains_filter_params(self, delivery_service, order_repo):
        admin = make_admin()
        insert_analytics_order(order_repo, traffic=TrafficCondition.HIGH)

        result = delivery_service.get_delivery_analytics(
            admin, traffic_condition="High", weather_condition="Sunny"
        )

        assert result.traffic_condition == "High"
        assert result.weather_condition == "Sunny"
