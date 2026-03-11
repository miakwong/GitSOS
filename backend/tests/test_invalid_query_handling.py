from fastapi.testclient import TestClient

from app.main import app
from app.schemas.search_filters import CurrentUser, Role
from app.routers import search_router


def fake_admin_user():
    return CurrentUser(
        user_id="admin1",
        role=Role.ADMIN,
        owner_restaurant_ids=[],
    )


def fake_load_rows():
    return [
        {
            "restaurant_id": "R1",
            "restaurant_name": "Sushi House",
            "city": "Kelowna",
            "cuisine": "Japanese",
            "customer_id": "C1",
            "order_id": "O1",
            "order_status": "Delivered",
            "order_value": "25.50",
            "item_name": "Salmon Roll",
            "category": "Sushi",
            "price": "12.50",
        },
        {
            "restaurant_id": "R2",
            "restaurant_name": "Burger Town",
            "city": "Vancouver",
            "cuisine": "Fast Food",
            "customer_id": "C2",
            "order_id": "O2",
            "order_status": "Placed",
            "order_value": "15.00",
            "item_name": "Cheeseburger",
            "category": "Burger",
            "price": "9.99",
        },
    ]


def setup_module():
    app.dependency_overrides[search_router.get_current_user_mock] = fake_admin_user
    search_router.service.repo.load_all_rows = fake_load_rows


def teardown_module():
    app.dependency_overrides.clear()


client = TestClient(app)


def test_restaurants_unsupported_filter_returns_400():
    response = client.get("/search/restaurants?bad_filter=test")

    assert response.status_code == 400
    body = response.json()

    assert "message" in body["detail"]
    assert body["detail"]["message"] == "Unsupported query parameter(s)."
    assert "bad_filter" in body["detail"]["unsupported"]


def test_menu_items_invalid_price_range_returns_400():
    response = client.get("/search/menu-items?min_price=100&max_price=10")

    assert response.status_code == 400
    body = response.json()

    assert body["detail"]["message"] == "Invalid price range."
    assert body["detail"]["reason"] == "min_price cannot be greater than max_price."


def test_orders_invalid_order_value_range_returns_400():
    response = client.get("/search/orders?min_order_value=80&max_order_value=10")

    assert response.status_code == 400
    body = response.json()

    assert body["detail"]["message"] == "Invalid order value range."
    assert body["detail"]["reason"] == "min_order_value cannot be greater than max_order_value."


def test_invalid_query_type_returns_400():
    response = client.get("/search/restaurants?page=abc")

    assert response.status_code == 400
    body = response.json()

    assert body["message"] == "Invalid request parameters."
    assert "details" in body


def test_error_response_does_not_expose_internal_details():
    response = client.get("/search/restaurants?bad_filter=test")

    assert response.status_code == 400
    body = response.json()

    assert "traceback" not in str(body).lower()
    assert "exception" not in str(body).lower()