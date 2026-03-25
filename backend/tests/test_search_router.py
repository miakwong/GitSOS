from app.routers import search_router
from app.schemas.search_filters import CurrentUser, Role
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()
app.include_router(search_router.router)
client = TestClient(app)


def fake_admin_user():
    return CurrentUser(user_id="admin1", role=Role.ADMIN, owner_restaurant_ids=[])


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


def setup_module():
    app.dependency_overrides[search_router.get_search_user] = fake_admin_user
    search_router.service.repo.load_all_rows = fake_load_rows


def teardown_module():
    app.dependency_overrides.clear()


client = TestClient(app)


def test_search_restaurants_success():
    response = client.get("/search/restaurants?city=Kelowna")

    assert response.status_code == 200
    body = response.json()

    assert "meta" in body
    assert "data" in body
    assert body["meta"]["total"] == 1
    assert body["data"][0]["restaurant_name"] == "Sushi House"


def test_search_restaurants_unsupported_filter():
    response = client.get("/search/restaurants?invalid_filter=abc")

    assert response.status_code == 422
    body = response.json()

    assert "detail" in body
    assert "Unsupported query parameter" in body["detail"]["message"]


def test_sort_restaurants_asc_returns_200():
    # Router should accept sort_by and sort_order as valid query params
    response = client.get("/search/restaurants?sort_by=restaurant_name&sort_order=asc")
    assert response.status_code == 200
    body = response.json()
    names = [r["restaurant_name"] for r in body["data"]]
    # Burger Town comes before Sushi House since it's ascending and B comes before S
    assert names.index("Burger Town") < names.index("Sushi House")


def test_sort_restaurants_desc_returns_200():
    response = client.get("/search/restaurants?sort_by=restaurant_name&sort_order=desc")
    assert response.status_code == 200
    body = response.json()
    names = [r["restaurant_name"] for r in body["data"]]
    # Sushi House comes before Burger Town when descending since S comes after B
    assert names.index("Sushi House") < names.index("Burger Town")


def test_invalid_sort_by_returns_400():
    # "city" is not a valid sort key for restaurants
    response = client.get("/search/restaurants?sort_by=city")
    assert response.status_code == 400


def test_invalid_sort_order_returns_422():
    # sort_order must be "asc" or "desc"
    response = client.get("/search/restaurants?sort_order=random")
    assert response.status_code == 422
