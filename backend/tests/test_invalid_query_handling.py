import pytest
import uuid
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.dependencies import get_current_user_full
from app.exception_handlers import request_validation_exception_handler
from app.main import app as main_app
from app.routers import search_router
from app.schemas.user import UserInDB

ADMIN_ID = uuid.uuid4()
MOCK_ADMIN = UserInDB(
    id=ADMIN_ID,
    email="admin@example.com",
    role="admin",
    password_hash="hashed",
)

FAKE_ROWS = [
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

# Separate app needed to register the custom RequestValidationError handler, 
# since the main app uses the default FastAPI handler which doesn't format the error response as expected by the tests
validation_app = FastAPI()
validation_app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
validation_app.include_router(search_router.router)
validation_app.dependency_overrides[search_router.get_search_user] = lambda: None

validation_client = TestClient(validation_app, raise_server_exceptions=False)

client = TestClient(main_app)


@pytest.fixture(autouse=True)
def override_auth():
    main_app.dependency_overrides[get_current_user_full] = lambda: MOCK_ADMIN
    yield
    main_app.dependency_overrides.clear()


def test_restaurants_unsupported_filter_returns_422(mocker):
    mocker.patch.object(search_router.service.repo, "load_all_rows", return_value=FAKE_ROWS)
    response = client.get("/search/restaurants?bad_filter=test")

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert body["detail"]["message"] == "Unsupported query parameter(s)."
    assert "bad_filter" in body["detail"]["unsupported"]


def test_menu_items_invalid_price_range_returns_422(mocker):
    mocker.patch.object(search_router.service.repo, "load_all_rows", return_value=FAKE_ROWS)
    response = client.get("/search/menu-items?min_price=100&max_price=10")

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["message"] == "Invalid price range."
    assert body["detail"]["reason"] == "min_price cannot be greater than max_price."


def test_orders_invalid_order_value_range_returns_422(mocker):
    mocker.patch.object(search_router.service.repo, "load_all_rows", return_value=FAKE_ROWS)
    response = client.get("/search/orders?min_order_value=80&max_order_value=10")

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["message"] == "Invalid order value range."
    assert body["detail"]["reason"] == "min_order_value cannot be greater than max_order_value."


def test_invalid_query_type_returns_422():
    # Uses the custom validation app so the RequestValidationError is formatted correctly
    response = validation_client.get("/search/restaurants?page=abc")

    assert response.status_code == 422
    body = response.json()
    assert body["message"] == "Invalid request parameters."
    assert "details" in body


def test_error_response_does_not_expose_internal_details(mocker):
    mocker.patch.object(search_router.service.repo, "load_all_rows", return_value=FAKE_ROWS)
    response = client.get("/search/restaurants?bad_filter=test")

    assert response.status_code == 422
    body = response.json()
    assert "traceback" not in str(body).lower()
    assert "exception" not in str(body).lower()
