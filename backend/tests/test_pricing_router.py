from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.routers import pricing_router


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


# Shared fake breakdown used by all inspect tests
FAKE_BREAKDOWN = {
    "order_id": "order-101",
    "food_price": 20.0,
    "delivery_fee": {
        "base_fee": 2.5,
        "distance_fee": 3.0,
        "method_fee": 0.5,
        "condition_fee": 0.0,
        "total_delivery_fee": 6.0,
    },
    "subtotal": 26.0,
    "tax": 1.30,
    "total": 27.30,
}


def fake_admin_user():
    return SimpleNamespace(id="admin-1", role="admin")


def fake_owner_user():
    return SimpleNamespace(id="owner-1", role="owner", restaurant_id=101)


def fake_customer_user():
    return SimpleNamespace(id="cust-1", role="customer")


def fake_inspect_returns_list(current_user, restaurant_id=None):
    # Simulates a successful response with one breakdown item
    return [FAKE_BREAKDOWN]


def fake_inspect_returns_empty(current_user, restaurant_id=None):
    return []


def fake_inspect_forbidden(current_user, restaurant_id=None):
    raise HTTPException(status_code=403, detail="Customers cannot inspect pricing")


def test_inspect_admin_returns_200():
    app.dependency_overrides[pricing_router.get_current_user] = fake_admin_user
    pricing_router.pricing_service.inspect_pricing = fake_inspect_returns_list

    response = client.get("/pricing/inspect")

    assert response.status_code == 200


def test_inspect_returns_list_of_breakdowns():
    app.dependency_overrides[pricing_router.get_current_user] = fake_admin_user
    pricing_router.pricing_service.inspect_pricing = fake_inspect_returns_list

    body = client.get("/pricing/inspect").json()

    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["order_id"] == "order-101"


def test_inspect_response_has_correct_fields():
    app.dependency_overrides[pricing_router.get_current_user] = fake_admin_user
    pricing_router.pricing_service.inspect_pricing = fake_inspect_returns_list

    body = client.get("/pricing/inspect").json()

    assert "order_id" in body[0]
    assert "food_price" in body[0]
    assert "delivery_fee" in body[0]
    assert "subtotal" in body[0]
    assert "tax" in body[0]
    assert "total" in body[0]


def test_inspect_owner_returns_200():
    app.dependency_overrides[pricing_router.get_current_user] = fake_owner_user
    pricing_router.pricing_service.inspect_pricing = fake_inspect_returns_list

    response = client.get("/pricing/inspect")

    assert response.status_code == 200


def test_inspect_customer_returns_403():
    app.dependency_overrides[pricing_router.get_current_user] = fake_customer_user
    pricing_router.pricing_service.inspect_pricing = fake_inspect_forbidden

    response = client.get("/pricing/inspect")

    assert response.status_code == 403
    assert response.json()["detail"] == "Customers cannot inspect pricing"


def test_inspect_with_restaurant_id_filter_returns_200():
    app.dependency_overrides[pricing_router.get_current_user] = fake_admin_user
    pricing_router.pricing_service.inspect_pricing = fake_inspect_returns_list

    response = client.get("/pricing/inspect?restaurant_id=101")

    assert response.status_code == 200


def test_inspect_no_orders_returns_empty_list():
    app.dependency_overrides[pricing_router.get_current_user] = fake_admin_user
    pricing_router.pricing_service.inspect_pricing = fake_inspect_returns_empty

    body = client.get("/pricing/inspect").json()

    assert body == []