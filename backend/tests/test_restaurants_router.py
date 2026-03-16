from unittest.mock import patch

import pytest
from app.main import app
from app.schemas.kaggle import KaggleMenuItem, KaggleRestaurant
from fastapi.testclient import TestClient

client = TestClient(app)

RESTAURANTS = [
    KaggleRestaurant(restaurant_id="10", name="Restaurant_10"),
    KaggleRestaurant(restaurant_id="20", name="Restaurant_20"),
]

MENU = [
    KaggleMenuItem(restaurant_id="10", food_item="Pasta", median_price=35.0),
    KaggleMenuItem(restaurant_id="10", food_item="Burger", median_price=20.0),
]


@pytest.fixture(autouse=True)
def mock_service():
    with patch("app.routers.restaurants.restaurant_service") as mock:
        mock.list_restaurants.return_value = RESTAURANTS
        mock.get_restaurant.side_effect = lambda rid: next(
            (r for r in RESTAURANTS if r.restaurant_id == rid), None
        )
        mock.get_menu.side_effect = lambda rid: [
            m for m in MENU if m.restaurant_id == rid
        ]
        # returns None for unknown restaurants 
        def _menu_for_restaurant(rid):
            if not any(r.restaurant_id == rid for r in RESTAURANTS):
                return None
            return [m for m in MENU if m.restaurant_id == rid]
        mock.get_menu_for_restaurant.side_effect = _menu_for_restaurant
        yield


# GET /restaurants
def test_list_restaurants_status_200():
    response = client.get("/restaurants")
    assert response.status_code == 200


def test_list_restaurants_returns_list():
    response = client.get("/restaurants")
    assert isinstance(response.json(), list)


def test_list_restaurants_count():
    response = client.get("/restaurants")
    assert len(response.json()) == 2


def test_list_restaurants_fields():
    data = client.get("/restaurants").json()
    assert data[0]["restaurant_id"] == "10"
    assert data[0]["name"] == "Restaurant_10"


# GET /restaurants/{id}
def test_get_restaurant_found():
    response = client.get("/restaurants/10")
    assert response.status_code == 200
    assert response.json()["restaurant_id"] == "10"


def test_get_restaurant_not_found():
    response = client.get("/restaurants/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Restaurant not found"

# GET /restaurants/{id}/menu
def test_get_menu_status_200():
    response = client.get("/restaurants/10/menu")
    assert response.status_code == 200


def test_get_menu_returns_items():
    data = client.get("/restaurants/10/menu").json()
    assert len(data) == 2


def test_get_menu_fields():
    data = client.get("/restaurants/10/menu").json()
    assert data[0]["food_item"] == "Pasta"
    assert data[0]["median_price"] == 35.0


def test_get_menu_unknown_restaurant_returns_404():
    response = client.get("/restaurants/999/menu")
    assert response.status_code == 404
    assert response.json()["detail"] == "Restaurant not found"


def test_get_menu_empty_for_restaurant_with_no_items():
    # restaurant 20 exists but has no menu items in fixture
    data = client.get("/restaurants/20/menu").json()
    assert data == []
