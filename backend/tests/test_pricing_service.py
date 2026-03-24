from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.order import (
    Order,
    OrderStatus,
    DeliveryMethod,
    TrafficCondition,
    WeatherCondition,
)
from app.services.pricing_service import PricingService


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


@pytest.fixture
def sample_order():
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


def test_get_price_breakdown_success(sample_order, customer_user):
    service = PricingService(
        order_repo=FakeOrderRepository(order=sample_order),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    result = service.get_price_breakdown(str(sample_order.order_id), customer_user)

    assert result.order_id == str(sample_order.order_id)
    assert result.food_price == 20.0
    assert result.delivery_fee.base_fee == 2.5
    assert result.delivery_fee.distance_fee == 3.0
    assert result.delivery_fee.method_fee == 0.5
    assert result.delivery_fee.condition_fee == 1.25
    assert result.delivery_fee.total_delivery_fee == 7.25
    assert result.subtotal == 27.25
    assert result.tax == 1.36
    assert result.total == 28.61


def test_get_price_breakdown_admin_can_view(sample_order, admin_user):
    service = PricingService(
        order_repo=FakeOrderRepository(order=sample_order),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    result = service.get_price_breakdown(str(sample_order.order_id), admin_user)

    assert result.order_id == str(sample_order.order_id)


def test_get_price_breakdown_forbidden_for_other_customer(sample_order, other_customer):
    service = PricingService(
        order_repo=FakeOrderRepository(order=sample_order),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_price_breakdown(str(sample_order.order_id), other_customer)

    assert exc_info.value.status_code == 403
    assert "permission" in exc_info.value.detail.lower()


def test_get_price_breakdown_rejects_historical_order(customer_user):
    service = PricingService(
        order_repo=FakeOrderRepository(order=None),
        kaggle_repo=FakeKaggleOrderRepository(order={"order_id": "K1"}),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_price_breakdown("K1", customer_user)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Order not found"


def test_get_price_breakdown_order_not_found(customer_user):
    service = PricingService(
        order_repo=FakeOrderRepository(order=None),
        kaggle_repo=FakeKaggleOrderRepository(order=None),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_price_breakdown("missing-order", customer_user)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Order not found"
