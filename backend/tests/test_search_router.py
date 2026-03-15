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
    app.dependency_overrides[search_router.get_current_user_mock] = fake_admin_user
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
