import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.dependencies import get_current_user
from app.main import app
from app.schemas.order import DeliveryMethod, Order, OrderStatus, TrafficCondition, WeatherCondition
from app.schemas.pricing import DeliveryFeeBreakdown, PriceBreakdownResponse, PricingAnalyticsResponse
from app.schemas.user import UserInDB

ORDER_ID = uuid.uuid4()
CUSTOMER_ID = uuid.uuid4()
ADMIN_ID = uuid.uuid4()

MOCK_CUSTOMER = UserInDB(
    id=CUSTOMER_ID,
    email="customer@example.com",
    role="customer",
    password_hash="hashed",
)

MOCK_ADMIN = UserInDB(
    id=ADMIN_ID,
    email="admin@example.com",
    role="admin",
    password_hash="hashed",
)

MOCK_ORDER = Order(
    order_id=ORDER_ID,
    customer_id=str(CUSTOMER_ID),
    restaurant_id=101,
    food_item="Burger",
    order_value=20.0,
    delivery_distance=4.0,
    delivery_method=DeliveryMethod.BIKE,
    traffic_condition=TrafficCondition.MEDIUM,
    weather_condition=WeatherCondition.RAINY,
    order_time="2026-03-16T12:00:00Z",
    order_status=OrderStatus.PLACED,
)

MOCK_BREAKDOWN = PriceBreakdownResponse(
    order_id=str(ORDER_ID),
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

MOCK_ANALYTICS = PricingAnalyticsResponse(
    total_orders=3,
    total_revenue=90.0,
    avg_order_value=30.0,
    min_order_value=20.0,
    max_order_value=40.0,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_auth_as_customer():
    app.dependency_overrides[get_current_user] = lambda: MOCK_CUSTOMER
    yield
    app.dependency_overrides.clear()


# ------------------------------------------------------------------ #
# Tests: price breakdown route
# ------------------------------------------------------------------ #

def test_get_price_breakdown_route_returns_200(mocker):
    """The endpoint should return HTTP 200 for a valid order."""
    mocker.patch("app.routers.pricing_router.pricing_service.get_price_breakdown", return_value=MOCK_BREAKDOWN)
    response = client.get(f"/pricing/orders/{ORDER_ID}/breakdown")
    assert response.status_code == 200


def test_get_price_breakdown_route_order_id_in_response(mocker):
    """The response body should include the correct order_id."""
    mocker.patch("app.routers.pricing_router.pricing_service.get_price_breakdown", return_value=MOCK_BREAKDOWN)
    body = client.get(f"/pricing/orders/{ORDER_ID}/breakdown").json()
    assert body["order_id"] == str(ORDER_ID)


def test_get_price_breakdown_route_food_price(mocker):
    """The response should include the food_price from Kaggle lookup."""
    mocker.patch("app.routers.pricing_router.pricing_service.get_price_breakdown", return_value=MOCK_BREAKDOWN)
    body = client.get(f"/pricing/orders/{ORDER_ID}/breakdown").json()
    assert body["food_price"] == 15.00


def test_get_price_breakdown_route_delivery_fee_breakdown(mocker):
    """All delivery fee sub-components should be present in the response."""
    mocker.patch("app.routers.pricing_router.pricing_service.get_price_breakdown", return_value=MOCK_BREAKDOWN)
    body = client.get(f"/pricing/orders/{ORDER_ID}/breakdown").json()
    fee = body["delivery_fee"]
    assert fee["base_fee"] == 3.00
    assert fee["distance_fee"] == 0.50
    assert fee["method_surcharge"] == 1.00
    assert fee["traffic_surcharge"] == 1.00
    assert fee["weather_surcharge"] == 1.50
    assert fee["condition_surcharge"] == 2.50
    assert fee["total_delivery_fee"] == 7.00


def test_get_price_breakdown_route_totals(mocker):
    """The subtotal, tax, and total should be correct."""
    mocker.patch("app.routers.pricing_router.pricing_service.get_price_breakdown", return_value=MOCK_BREAKDOWN)
    body = client.get(f"/pricing/orders/{ORDER_ID}/breakdown").json()
    assert body["subtotal"] == 22.00
    assert body["tax"] == 1.10
    assert body["total"] == 23.10


def test_get_price_breakdown_route_returns_404_for_missing_order(mocker):
    """A non-existent order_id should return 404."""
    mocker.patch(
        "app.routers.pricing_router.pricing_service.get_price_breakdown",
        side_effect=HTTPException(status_code=404, detail="Order not found"),
    )
    response = client.get(f"/pricing/orders/{uuid.uuid4()}/breakdown")
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_get_price_breakdown_route_returns_403_for_wrong_customer(mocker):
    """A customer who did not place the order should get 403."""
    mocker.patch(
        "app.routers.pricing_router.pricing_service.get_price_breakdown",
        side_effect=HTTPException(status_code=403, detail="You do not have permission to view this order breakdown"),
    )
    response = client.get(f"/pricing/orders/{ORDER_ID}/breakdown")
    assert response.status_code == 403


# ------------------------------------------------------------------ #
# Tests: analytics route
# ------------------------------------------------------------------ #

def test_analytics_route_admin_returns_200(mocker):
    """Admin should be able to access the analytics endpoint."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_ADMIN
    mocker.patch("app.routers.pricing_router.pricing_service.get_pricing_analytics", return_value=MOCK_ANALYTICS)
    response = client.get("/pricing/analytics")
    assert response.status_code == 200


def test_analytics_route_returns_correct_fields(mocker):
    """The analytics response should contain all required fields."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_ADMIN
    mocker.patch("app.routers.pricing_router.pricing_service.get_pricing_analytics", return_value=MOCK_ANALYTICS)
    body = client.get("/pricing/analytics").json()
    assert "total_orders" in body
    assert "total_revenue" in body
    assert "avg_order_value" in body
    assert "min_order_value" in body
    assert "max_order_value" in body


def test_analytics_route_returns_correct_values(mocker):
    """The analytics response values should match what the service returns."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_ADMIN
    mocker.patch("app.routers.pricing_router.pricing_service.get_pricing_analytics", return_value=MOCK_ANALYTICS)
    body = client.get("/pricing/analytics").json()
    assert body["total_orders"] == 3
    assert body["total_revenue"] == 90.0
    assert body["avg_order_value"] == 30.0


def test_analytics_route_customer_returns_403(mocker):
    """Non-admin users should be denied access to analytics."""
    mocker.patch(
        "app.routers.pricing_router.pricing_service.get_pricing_analytics",
        side_effect=HTTPException(status_code=403, detail="Only admins can view pricing analytics"),
    )
    response = client.get("/pricing/analytics")
    assert response.status_code == 403
    assert response.json()["detail"] == "Only admins can view pricing analytics"
