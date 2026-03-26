import pytest
import uuid
from fastapi.testclient import TestClient

from app.dependencies import get_current_user_full
from app.main import app
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
    },
]

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user_full] = lambda: MOCK_ADMIN
    yield
    app.dependency_overrides.clear()


def test_search_restaurants_success(mocker):
    mocker.patch.object(search_router.service.repo, "load_all_rows", return_value=FAKE_ROWS)
    response = client.get("/search/restaurants?city=Kelowna")

    assert response.status_code == 200
    body = response.json()
    assert "meta" in body
    assert "data" in body
    assert body["meta"]["total"] == 1
    assert body["data"][0]["restaurant_name"] == "Sushi House"


def test_search_restaurants_unsupported_filter(mocker):
    mocker.patch.object(search_router.service.repo, "load_all_rows", return_value=FAKE_ROWS)
    response = client.get("/search/restaurants?invalid_filter=abc")

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert "Unsupported query parameter" in body["detail"]["message"]


def test_sort_restaurants_asc_returns_200(mocker):
    mocker.patch.object(search_router.service.repo, "load_all_rows", return_value=FAKE_ROWS)
    response = client.get("/search/restaurants?sort_by=restaurant_name&sort_order=asc")

    assert response.status_code == 200
    names = [r["restaurant_name"] for r in response.json()["data"]]
    # Burger Town comes before Sushi House in ascending order, since B comes before S
    assert names.index("Burger Town") < names.index("Sushi House")


def test_sort_restaurants_desc_returns_200(mocker):
    mocker.patch.object(search_router.service.repo, "load_all_rows", return_value=FAKE_ROWS)
    response = client.get("/search/restaurants?sort_by=restaurant_name&sort_order=desc")

    assert response.status_code == 200
    names = [r["restaurant_name"] for r in response.json()["data"]]
    # Sushi House comes before Burger Town in descending order, since S comes after B
    assert names.index("Sushi House") < names.index("Burger Town")


def test_invalid_sort_by_returns_400(mocker):
    mocker.patch.object(search_router.service.repo, "load_all_rows", return_value=FAKE_ROWS)
    # "city" is not a valid sort key for restaurants
    response = client.get("/search/restaurants?sort_by=city")

    assert response.status_code == 400


def test_invalid_sort_order_returns_422():
    # sort_order must be "asc" or "desc"
    response = client.get("/search/restaurants?sort_order=random")

    assert response.status_code == 422
