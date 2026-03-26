from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.routers import pricing_router
from app.schemas.pricing import DeliveryFeeBreakdown, PriceBreakdownResponse


# ------------------------------------------------------------------ #
# Fake auth: always returns a logged-in customer
# ------------------------------------------------------------------ #

def fake_current_user():
    return SimpleNamespace(id="customer-1", role="customer")


# ------------------------------------------------------------------ #
# Fake service response using the updated schema fields
# ------------------------------------------------------------------ #

FAKE_ORDER_ID = "test-order-123"

def fake_get_price_breakdown(order_id: str, current_user):
    return PriceBreakdownResponse(
        order_id=order_id,
        food_price=15.00,
        delivery_fee=DeliveryFeeBreakdown(
            base_fee=3.00,
            distance_fee=0.50,
            method_surcharge=1.00,
            traffic_surcharge=1.00,
            weather_surcharge=1.50,
            condition_surcharge=2.50,
            total_delivery_fee=7.00,
        ),
        subtotal=22.00,
        tax=1.10,
        total=23.10,
    )


# ------------------------------------------------------------------ #
# Test app setup
# ------------------------------------------------------------------ #

app = FastAPI()
app.include_router(pricing_router.router)

app.dependency_overrides[pricing_router.get_current_user] = fake_current_user
pricing_router.pricing_service.get_price_breakdown = fake_get_price_breakdown

client = TestClient(app)


# ------------------------------------------------------------------ #
# Tests: price breakdown route
# ------------------------------------------------------------------ #

def test_get_price_breakdown_route_returns_200():
    """The endpoint should return HTTP 200 for a valid order."""
    response = client.get(f"/pricing/orders/{FAKE_ORDER_ID}/breakdown")
    assert response.status_code == 200


def test_get_price_breakdown_route_order_id_in_response():
    """The response body should include the correct order_id."""
    response = client.get(f"/pricing/orders/{FAKE_ORDER_ID}/breakdown")
    body = response.json()
    assert body["order_id"] == FAKE_ORDER_ID


def test_get_price_breakdown_route_food_price():
    """The response should include the food_price from Kaggle lookup."""
    body = client.get(f"/pricing/orders/{FAKE_ORDER_ID}/breakdown").json()
    assert body["food_price"] == 15.00


def test_get_price_breakdown_route_delivery_fee_breakdown():
    """All delivery fee sub-components should be present in the response."""
    body = client.get(f"/pricing/orders/{FAKE_ORDER_ID}/breakdown").json()
    fee = body["delivery_fee"]

    assert fee["base_fee"] == 3.00
    assert fee["distance_fee"] == 0.50
    assert fee["method_surcharge"] == 1.00
    assert fee["traffic_surcharge"] == 1.00
    assert fee["weather_surcharge"] == 1.50
    assert fee["condition_surcharge"] == 2.50
    assert fee["total_delivery_fee"] == 7.00


def test_get_price_breakdown_route_totals():
    """The subtotal, tax, and total should be correct."""
    body = client.get(f"/pricing/orders/{FAKE_ORDER_ID}/breakdown").json()
    assert body["subtotal"] == 22.00
    assert body["tax"] == 1.10
    assert body["total"] == 23.10


# ------------------------------------------------------------------ #
# Tests: analytics route
# ------------------------------------------------------------------ #

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
