from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.order import (
    DeliveryMethod,
    Order,
    OrderStatus,
    TrafficCondition,
    WeatherCondition,
)
from app.services.pricing_service import PricingService


# ------------------------------------------------------------------ #
# Fake repositories — no real files touched
# ------------------------------------------------------------------ #

class FakeOrderRepository:
    def __init__(self, order=None):
        self.order = order

    def get_order_by_id(self, order_id: str):
        return self.order


class FakeKaggleOrderRepository:
    def __init__(self, order=None):
        self.order = order

    def get_order_by_id(self, order_id: str):
        return self.order


# ------------------------------------------------------------------ #
# Shared fixtures
# ------------------------------------------------------------------ #

@pytest.fixture
def sample_order():
    """
    A system-created order used across multiple tests.
    Delivery parameters chosen so the math is easy to verify:
      - distance = 4.0  -> tier 2: (4.0 - 3.0) * $0.50 = $0.50
      - method = Bike   -> $1.00
      - traffic = Medium -> $1.00
      - weather = Rainy  -> $1.50
    """
    return Order(
        order_id=uuid4(),
        customer_id="customer-1",
        restaurant_id=101,
        food_item="Burger",
        order_time="2026-03-16T12:00:00Z",
        order_value=20.0,
        delivery_distance=4.0,
        delivery_method=DeliveryMethod.BIKE,
        traffic_condition=TrafficCondition.MEDIUM,
        weather_condition=WeatherCondition.RAINY,
        order_status=OrderStatus.PLACED,
    )


@pytest.fixture
def customer_user():
    return SimpleNamespace(id="customer-1", role="customer")


@pytest.fixture
def other_customer():
    return SimpleNamespace(id="someone-else", role="customer")


@pytest.fixture
def admin_user():
    return SimpleNamespace(id="admin-1", role="admin")


# ------------------------------------------------------------------ #
# Test: successful price breakdown — verify every number
# ------------------------------------------------------------------ #

def test_get_price_breakdown_success(sample_order, customer_user):
    """
    With get_median_price mocked to return $15.00 we can verify
    every calculated number exactly.

    Expected:
      food_price          = $15.00  (from Kaggle mock)
      base_fee            = $3.00
      distance_fee        = (4.0 - 3.0) * 0.50 = $0.50
      method_surcharge    = $1.00  (Bike)
      traffic_surcharge   = $1.00  (Medium)
      weather_surcharge   = $1.50  (Rainy)
      condition_surcharge = $2.50  (traffic + weather)
      total_delivery_fee  = $7.00  (3.00 + 0.50 + 1.00 + 2.50)
      subtotal            = $22.00 (15.00 + 7.00)
      tax                 = $1.10  (22.00 * 5%)
      total               = $23.10 (22.00 + 1.10)
    """
    service = PricingService(
        order_repo=FakeOrderRepository(order=sample_order),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    with patch("app.services.pricing_service.get_median_price", return_value=15.00):
        result = service.get_price_breakdown(str(sample_order.order_id), customer_user)

    assert result.order_id == str(sample_order.order_id)
    assert result.food_price == 15.00

    # Delivery fee itemized
    assert result.delivery_fee.base_fee == 3.00
    assert result.delivery_fee.distance_fee == 0.50
    assert result.delivery_fee.method_surcharge == 1.00
    assert result.delivery_fee.traffic_surcharge == 1.00
    assert result.delivery_fee.weather_surcharge == 1.50
    assert result.delivery_fee.condition_surcharge == 2.50
    assert result.delivery_fee.total_delivery_fee == 7.00

    # Final totals
    assert result.subtotal == 22.00
    assert result.tax == 1.10
    assert result.total == 23.10


# ------------------------------------------------------------------ #
# Test: access control
# ------------------------------------------------------------------ #

def test_get_price_breakdown_admin_can_view_any_order(sample_order, admin_user):
    """Admin should be able to see any order's breakdown."""
    service = PricingService(
        order_repo=FakeOrderRepository(order=sample_order),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    with patch("app.services.pricing_service.get_median_price", return_value=15.00):
        result = service.get_price_breakdown(str(sample_order.order_id), admin_user)

    assert result.order_id == str(sample_order.order_id)


def test_get_price_breakdown_forbidden_for_other_customer(sample_order, other_customer):
    """A customer who did not place the order should get 403."""
    service = PricingService(
        order_repo=FakeOrderRepository(order=sample_order),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_price_breakdown(str(sample_order.order_id), other_customer)

    assert exc_info.value.status_code == 403
    assert "permission" in exc_info.value.detail.lower()


# ------------------------------------------------------------------ #
# Test: Kaggle historical orders are rejected
# ------------------------------------------------------------------ #

def test_get_price_breakdown_rejects_historical_order(customer_user):
    """Kaggle historical orders must never be priced — return 404 to avoid leaking the ID exists."""
    service = PricingService(
        order_repo=FakeOrderRepository(order=None),
        kaggle_repo=FakeKaggleOrderRepository(order={"order_id": "K1"}),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_price_breakdown("K1", customer_user)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Order not found"


# ------------------------------------------------------------------ #
# Test: order not found at all
# ------------------------------------------------------------------ #

def test_get_price_breakdown_order_not_found(customer_user):
    """When the order_id doesn't exist anywhere, return 404."""
    service = PricingService(
        order_repo=FakeOrderRepository(order=None),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_price_breakdown("missing-order", customer_user)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Order not found"


# ------------------------------------------------------------------ #
# Test: distance fee progressive tiers
# ------------------------------------------------------------------ #

def test_distance_fee_tier1_no_fee():
    """2.0 <= distance < 3.0 → $0.00"""
    service = PricingService()
    assert service._calculate_distance_fee(2.0) == 0.00
    assert service._calculate_distance_fee(2.9) == 0.00


def test_distance_fee_tier2_lower_boundary():
    """At exactly 3.0 km, tier 2 starts: (3.0 - 3.0) * 0.50 = $0.00"""
    service = PricingService()
    assert service._calculate_distance_fee(3.0) == 0.00


def test_distance_fee_tier2_mid():
    """5.0 km in tier 2: (5.0 - 3.0) * 0.50 = $1.00"""
    service = PricingService()
    assert service._calculate_distance_fee(5.0) == 1.00


def test_distance_fee_tier3_lower_boundary():
    """At exactly 8.0 km, tier 3 starts: $2.50 + (8.0 - 8.0) * 0.80 = $2.50"""
    service = PricingService()
    assert service._calculate_distance_fee(8.0) == 2.50


def test_distance_fee_tier3_mid():
    """10.0 km in tier 3: $2.50 + (10.0 - 8.0) * 0.80 = $4.10"""
    service = PricingService()
    assert service._calculate_distance_fee(10.0) == 4.10


def test_distance_fee_tier3_upper_boundary():
    """At exactly 15.0 km (max): $2.50 + (15.0 - 8.0) * 0.80 = $8.10"""
    service = PricingService()
    # Use pytest.approx to handle floating point precision (e.g. 1.234500000000001)
    assert service._calculate_distance_fee(15.0) == pytest.approx(8.10)


# ------------------------------------------------------------------ #
# Test: method surcharges
# ------------------------------------------------------------------ #

def test_method_surcharge_walk():
    assert PricingService()._calculate_method_surcharge(DeliveryMethod.WALK) == 0.00


def test_method_surcharge_bike():
    assert PricingService()._calculate_method_surcharge(DeliveryMethod.BIKE) == 1.00


def test_method_surcharge_car():
    assert PricingService()._calculate_method_surcharge(DeliveryMethod.CAR) == 2.50


# ------------------------------------------------------------------ #
# Test: traffic surcharges
# ------------------------------------------------------------------ #

def test_traffic_surcharge_low():
    assert PricingService()._calculate_traffic_surcharge(TrafficCondition.LOW) == 0.00


def test_traffic_surcharge_medium():
    assert PricingService()._calculate_traffic_surcharge(TrafficCondition.MEDIUM) == 1.00


def test_traffic_surcharge_high():
    assert PricingService()._calculate_traffic_surcharge(TrafficCondition.HIGH) == 2.00


# ------------------------------------------------------------------ #
# Test: weather surcharges
# ------------------------------------------------------------------ #

def test_weather_surcharge_sunny():
    assert PricingService()._calculate_weather_surcharge(WeatherCondition.SUNNY) == 0.00


def test_weather_surcharge_rainy():
    assert PricingService()._calculate_weather_surcharge(WeatherCondition.RAINY) == 1.50


def test_weather_surcharge_snowy():
    assert PricingService()._calculate_weather_surcharge(WeatherCondition.SNOWY) == 2.00


# ------------------------------------------------------------------ #
# Test: pricing is deterministic — same inputs always give same output
# ------------------------------------------------------------------ #

def test_pricing_is_deterministic(sample_order, customer_user):
    """
    Calling get_price_breakdown twice with the same order must return
    the exact same numbers — no randomness allowed.
    """
    service = PricingService(
        order_repo=FakeOrderRepository(order=sample_order),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    with patch("app.services.pricing_service.get_median_price", return_value=15.00):
        result1 = service.get_price_breakdown(str(sample_order.order_id), customer_user)
        result2 = service.get_price_breakdown(str(sample_order.order_id), customer_user)

    assert result1.food_price == result2.food_price
    assert result1.delivery_fee.total_delivery_fee == result2.delivery_fee.total_delivery_fee
    assert result1.total == result2.total


# ------------------------------------------------------------------ #
# Analytics tests fixtures
# ------------------------------------------------------------------ #

class FakeOrderRepoForAnalytics:
    def __init__(self, orders):
        self.orders = orders

    def get_all_orders(self):
        return self.orders

    def get_order_by_id(self, order_id: str):
        for o in self.orders:
            if str(o.order_id) == order_id:
                return o
        return None


@pytest.fixture
def analytics_admin():
    return SimpleNamespace(id="admin-1", role="admin")


@pytest.fixture
def analytics_customer():
    return SimpleNamespace(id="cust-1", role="customer")


@pytest.fixture
def analytics_owner():
    return SimpleNamespace(id="owner-1", role="owner", restaurant_id=101)


@pytest.fixture
def two_orders():
    order_a = Order(
        order_id=uuid4(),
        customer_id="C1",
        restaurant_id=101,
        food_item="Burger",
        order_time="2026-03-16T12:00:00Z",
        order_value=20.0,
        delivery_distance=4.0,
        delivery_method=DeliveryMethod.BIKE,
        traffic_condition=TrafficCondition.LOW,
        weather_condition=WeatherCondition.SUNNY,
        order_status=OrderStatus.PLACED,
    )
    order_b = Order(
        order_id=uuid4(),
        customer_id="C2",
        restaurant_id=102,
        food_item="Pizza",
        order_time="2026-03-16T13:00:00Z",
        order_value=40.0,
        delivery_distance=6.0,
        delivery_method=DeliveryMethod.CAR,
        traffic_condition=TrafficCondition.HIGH,
        weather_condition=WeatherCondition.RAINY,
        order_status=OrderStatus.PLACED,
    )
    return [order_a, order_b]


def test_analytics_admin_can_access(analytics_admin, two_orders):
    service = PricingService(
        order_repo=FakeOrderRepoForAnalytics(orders=two_orders),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    with patch("app.services.pricing_service.get_median_price", return_value=15.00):
        result = service.get_pricing_analytics(analytics_admin)

    assert result is not None


def test_analytics_total_orders(analytics_admin, two_orders):
    service = PricingService(
        order_repo=FakeOrderRepoForAnalytics(orders=two_orders),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    with patch("app.services.pricing_service.get_median_price", return_value=15.00):
        result = service.get_pricing_analytics(analytics_admin)

    assert result.total_orders == 2


def test_analytics_min_max_avg_order_value(analytics_admin, two_orders):
    """
    With get_median_price mocked to $15.00:
      order_a (Bike, 4km, Low, Sunny):  $15 + $4.50 delivery = $19.50, tax $0.98 -> total $20.48
      order_b (Car,  6km, High, Rainy): $15 + $10.50 delivery = $25.50, tax $1.28 -> total $26.78
    """
    service = PricingService(
        order_repo=FakeOrderRepoForAnalytics(orders=two_orders),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    with patch("app.services.pricing_service.get_median_price", return_value=15.00):
        result = service.get_pricing_analytics(analytics_admin)

    assert result.min_order_value == 20.48
    assert result.max_order_value == 26.78
    assert result.avg_order_value == round(result.total_revenue / result.total_orders, 2)
    assert result.min_order_value < result.max_order_value


def test_analytics_total_revenue_is_positive(analytics_admin, two_orders):
    """total_revenue = $20.48 + $26.78 = $47.26 (both orders use Kaggle price)"""
    service = PricingService(
        order_repo=FakeOrderRepoForAnalytics(orders=two_orders),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    with patch("app.services.pricing_service.get_median_price", return_value=15.00):
        result = service.get_pricing_analytics(analytics_admin)

    assert result.total_revenue == 47.26


def test_analytics_empty_orders(analytics_admin):
    service = PricingService(
        order_repo=FakeOrderRepoForAnalytics(orders=[]),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    result = service.get_pricing_analytics(analytics_admin)

    assert result.total_orders == 0
    assert result.total_revenue == 0.0
    assert result.avg_order_value is None
    assert result.min_order_value is None
    assert result.max_order_value is None


def test_analytics_customer_is_denied(analytics_customer, two_orders):
    service = PricingService(
        order_repo=FakeOrderRepoForAnalytics(orders=two_orders),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_pricing_analytics(analytics_customer)

    assert exc_info.value.status_code == 403


def test_analytics_owner_is_denied(analytics_owner, two_orders):
    service = PricingService(
        order_repo=FakeOrderRepoForAnalytics(orders=two_orders),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_pricing_analytics(analytics_owner)

    assert exc_info.value.status_code == 403
