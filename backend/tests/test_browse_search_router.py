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

MENU_ITEMS = [
    KaggleMenuItem(restaurant_id="10", food_item="Beef Burger", median_price=12.0),
    KaggleMenuItem(restaurant_id="20", food_item="Veggie Burger", median_price=10.0),
]


@pytest.fixture(autouse=True)
def mock_svc():
    with patch("app.routers.restaurants.restaurant_service") as mock:
        mock.list_restaurants.return_value = RESTAURANTS
        mock.get_restaurant.side_effect = lambda rid: next(
            (r for r in RESTAURANTS if r.restaurant_id == rid), None
        )
        mock.get_menu_for_restaurant.side_effect = lambda rid: (
            [m for m in MENU_ITEMS if m.restaurant_id == rid]
            if any(r.restaurant_id == rid for r in RESTAURANTS)
            else None
        )
        mock.search_menu.return_value = MENU_ITEMS
        yield mock


def test_search_menu_200(mock_svc):
    response = client.get("/restaurants/menu/search?food_item=Burger")
    assert response.status_code == 200


def test_search_menu_returns_list(mock_svc):
    data = client.get("/restaurants/menu/search?food_item=Burger").json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_search_menu_item_fields(mock_svc):
    data = client.get("/restaurants/menu/search?food_item=Burger").json()
    assert data[0]["food_item"] == "Beef Burger"
    assert "restaurant_id" in data[0]
    assert "median_price" in data[0]


def test_search_menu_no_results(mock_svc):
    mock_svc.search_menu.return_value = []
    data = client.get("/restaurants/menu/search?food_item=Sushi").json()
    assert data == []


def test_search_menu_missing_param_422():
    response = client.get("/restaurants/menu/search")
    assert response.status_code == 422


def test_search_menu_empty_keyword_422():
    response = client.get("/restaurants/menu/search?food_item=")
    assert response.status_code == 422


def test_search_menu_calls_service(mock_svc):
    client.get("/restaurants/menu/search?food_item=Burger")
    mock_svc.search_menu.assert_called_once_with("Burger")


def test_search_menu_does_not_conflict_with_restaurant_id_route(mock_svc):
    response = client.get("/restaurants/10")
    assert response.status_code == 200
    assert response.json()["restaurant_id"] == "10"


def test_list_restaurants_still_works(mock_svc):
    response = client.get("/restaurants")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_menu_still_works(mock_svc):
    response = client.get("/restaurants/10/menu")
    assert response.status_code == 200
