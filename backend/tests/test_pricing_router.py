from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import pricing_router
from app.schemas.order import (
    Order,
    OrderStatus,
    DeliveryMethod,
    TrafficCondition,
    WeatherCondition,
)


def fake_current_user():
    return SimpleNamespace(id="customer-1", role="customer")


def fake_get_price_breakdown(order_id: str, current_user):
    return {
        "order_id": order_id,
        "food_price": 20.0,
        "delivery_fee": {
            "base_fee": 2.5,
            "distance_fee": 3.0,
            "method_fee": 0.5,
            "condition_fee": 1.25,
            "total_delivery_fee": 7.25,
        },
        "subtotal": 27.25,
        "tax": 1.36,
        "total": 28.61,
    }


app = FastAPI()
app.include_router(pricing_router.router)

app.dependency_overrides[pricing_router.get_current_user] = fake_current_user
pricing_router.pricing_service.get_price_breakdown = fake_get_price_breakdown

client = TestClient(app)


def test_get_price_breakdown_route_success():
    response = client.get("/pricing/orders/test-order-123/breakdown")

    assert response.status_code == 200
    body = response.json()

    assert body["order_id"] == "test-order-123"
    assert body["food_price"] == 20.0
    assert body["delivery_fee"]["total_delivery_fee"] == 7.25
    assert body["subtotal"] == 27.25
    assert body["tax"] == 1.36
    assert body["total"] == 28.61


def fake_analytics_admin():
    return SimpleNamespace(id="admin-1", role="admin")


def fake_analytics_customer():
    return SimpleNamespace(id="cust-1", role="customer")


def fake_get_pricing_analytics_success(current_user):
    from app.schemas.pricing import PricingAnalyticsResponse
    return PricingAnalyticsResponse(
        total_orders=3,
        total_revenue=90.0,
        avg_order_value=30.0,
        min_order_value=20.0,
        max_order_value=40.0,
    )


def fake_get_pricing_analytics_forbidden(current_user):
    from fastapi import HTTPException
    raise HTTPException(status_code=403, detail="Only admins can view pricing analytics")


def test_analytics_route_admin_returns_200():
    app.dependency_overrides[pricing_router.get_current_user] = fake_analytics_admin
    pricing_router.pricing_service.get_pricing_analytics = fake_get_pricing_analytics_success

    response = client.get("/pricing/analytics")

    assert response.status_code == 200


def test_analytics_route_returns_correct_fields():
    app.dependency_overrides[pricing_router.get_current_user] = fake_analytics_admin
    pricing_router.pricing_service.get_pricing_analytics = fake_get_pricing_analytics_success

    body = client.get("/pricing/analytics").json()

    assert "total_orders" in body
    assert "total_revenue" in body
    assert "avg_order_value" in body
    assert "min_order_value" in body
    assert "max_order_value" in body


def test_analytics_route_returns_correct_values():
    app.dependency_overrides[pricing_router.get_current_user] = fake_analytics_admin
    pricing_router.pricing_service.get_pricing_analytics = fake_get_pricing_analytics_success

    body = client.get("/pricing/analytics").json()

    assert body["total_orders"] == 3
    assert body["total_revenue"] == 90.0
    assert body["avg_order_value"] == 30.0


def test_analytics_route_customer_returns_403():
    app.dependency_overrides[pricing_router.get_current_user] = fake_analytics_customer
    pricing_router.pricing_service.get_pricing_analytics = fake_get_pricing_analytics_forbidden

    response = client.get("/pricing/analytics")

    assert response.status_code == 403
    assert response.json()["detail"] == "Only admins can view pricing analytics"