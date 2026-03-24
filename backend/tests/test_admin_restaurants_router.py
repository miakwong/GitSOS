from unittest.mock import patch
from uuid import uuid4

import pytest
from app.dependencies import get_current_admin
from app.main import app
from app.schemas.kaggle import KaggleMenuItem, KaggleRestaurant
from app.schemas.menu import MenuItemOut
from app.schemas.restaurant_profile import RestaurantProfileOut
from fastapi import HTTPException
from fastapi.testclient import TestClient

client = TestClient(app)

ADMIN_ID = uuid4()
RESTAURANT_ID = "10"

RESTAURANT = KaggleRestaurant(restaurant_id=RESTAURANT_ID, name="Restaurant_10")
KAGGLE_MENU = [KaggleMenuItem(restaurant_id=RESTAURANT_ID, food_item="Burger", median_price=12.0)]
MENU_ITEM = MenuItemOut(restaurant_id=RESTAURANT_ID, food_item="Burger", price=12.0)
PROFILE = RestaurantProfileOut(restaurant_id=RESTAURANT_ID, name="Restaurant_10")


@pytest.fixture(autouse=True)
def mock_admin():
    app.dependency_overrides[get_current_admin] = lambda: ADMIN_ID
    yield
    app.dependency_overrides.pop(get_current_admin, None)


@pytest.fixture(autouse=True)
def mock_services():
    with patch("app.routers.admin.restaurant_service") as mock_rest, \
         patch("app.routers.admin.menu_service") as mock_menu:
        mock_rest.list_restaurants.return_value = [RESTAURANT]
        mock_rest.get_restaurant.return_value = RESTAURANT
        mock_rest.get_menu_for_restaurant.return_value = KAGGLE_MENU
        mock_rest.get_profile.return_value = PROFILE
        mock_rest.update_profile.return_value = PROFILE
        mock_menu.get_menu_items.return_value = [MENU_ITEM]
        mock_menu.create_menu_item.return_value = MENU_ITEM
        mock_menu.update_menu_item.return_value = MENU_ITEM
        mock_menu.delete_menu_item.return_value = True
        yield mock_rest, mock_menu


# GET /admin/restaurants

def test_admin_list_restaurants_200():
    response = client.get("/admin/restaurants")
    assert response.status_code == 200


def test_admin_list_restaurants_returns_data():
    data = client.get("/admin/restaurants").json()
    assert isinstance(data, list)
    assert data[0]["restaurant_id"] == RESTAURANT_ID


def test_admin_list_restaurants_no_auth_401():
    app.dependency_overrides.pop(get_current_admin, None)
    response = client.get("/admin/restaurants")
    app.dependency_overrides[get_current_admin] = lambda: ADMIN_ID
    assert response.status_code == 401


# GET /admin/restaurants/{id}

def test_admin_get_restaurant_200():
    response = client.get(f"/admin/restaurants/{RESTAURANT_ID}")
    assert response.status_code == 200


def test_admin_get_restaurant_fields():
    data = client.get(f"/admin/restaurants/{RESTAURANT_ID}").json()
    assert data["restaurant_id"] == RESTAURANT_ID
    assert data["name"] == "Restaurant_10"


def test_admin_get_restaurant_not_found(mock_services):
    mock_rest, _ = mock_services
    mock_rest.get_restaurant.return_value = None
    response = client.get("/admin/restaurants/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Restaurant not found"


# GET /admin/restaurants/{id}/menu

def test_admin_get_menu_200():
    response = client.get(f"/admin/restaurants/{RESTAURANT_ID}/menu")
    assert response.status_code == 200


def test_admin_get_menu_returns_items():
    data = client.get(f"/admin/restaurants/{RESTAURANT_ID}/menu").json()
    assert len(data) == 1
    assert data[0]["food_item"] == "Burger"


def test_admin_get_menu_not_found(mock_services):
    mock_rest, _ = mock_services
    mock_rest.get_menu_for_restaurant.return_value = None
    response = client.get("/admin/restaurants/999/menu")
    assert response.status_code == 404


# GET /admin/restaurants/{id}/menu/items

def test_admin_list_menu_items_200():
    response = client.get(f"/admin/restaurants/{RESTAURANT_ID}/menu/items")
    assert response.status_code == 200


def test_admin_list_menu_items_returns_data():
    data = client.get(f"/admin/restaurants/{RESTAURANT_ID}/menu/items").json()
    assert data[0]["food_item"] == "Burger"
    assert data[0]["price"] == 12.0


# POST /admin/restaurants/{id}/menu/items

def test_admin_create_menu_item_201():
    response = client.post(
        f"/admin/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "Burger", "price": 12.0},
    )
    assert response.status_code == 201


def test_admin_create_menu_item_returns_item():
    data = client.post(
        f"/admin/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "Burger", "price": 12.0},
    ).json()
    assert data["food_item"] == "Burger"


def test_admin_create_menu_item_invalid_restaurant(mock_services):
    mock_rest, mock_menu = mock_services
    mock_menu.create_menu_item.side_effect = HTTPException(status_code=404, detail="Restaurant not found")
    response = client.post(
        "/admin/restaurants/999/menu/items",
        json={"food_item": "Burger", "price": 12.0},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Restaurant not found"


def test_admin_create_menu_item_empty_food_item_422():
    response = client.post(
        f"/admin/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "", "price": 12.0},
    )
    assert response.status_code == 422


def test_admin_create_menu_item_missing_price_422():
    response = client.post(
        f"/admin/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "Burger"},
    )
    assert response.status_code == 422


def test_admin_create_menu_item_zero_price_422():
    response = client.post(
        f"/admin/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "Burger", "price": 0},
    )
    assert response.status_code == 422


# PUT /admin/restaurants/{id}/menu/items/{food_item}

def test_admin_update_menu_item_200():
    response = client.put(
        f"/admin/restaurants/{RESTAURANT_ID}/menu/items/Burger",
        json={"price": 15.0},
    )
    assert response.status_code == 200


def test_admin_update_menu_item_not_found(mock_services):
    _, mock_menu = mock_services
    mock_menu.update_menu_item.return_value = None
    response = client.put(
        f"/admin/restaurants/{RESTAURANT_ID}/menu/items/NonExistent",
        json={"price": 15.0},
    )
    assert response.status_code == 404


def test_admin_update_menu_item_any_restaurant(mock_services):
    _, mock_menu = mock_services
    response = client.put(
        "/admin/restaurants/99/menu/items/Burger",
        json={"price": 15.0},
    )
    assert response.status_code == 200


def test_admin_update_menu_item_negative_price_422():
    response = client.put(
        f"/admin/restaurants/{RESTAURANT_ID}/menu/items/Burger",
        json={"price": -5.0},
    )
    assert response.status_code == 422


# DELETE /admin/restaurants/{id}/menu/items/{food_item}

def test_admin_delete_menu_item_204():
    response = client.delete(f"/admin/restaurants/{RESTAURANT_ID}/menu/items/Burger")
    assert response.status_code == 204


def test_admin_delete_menu_item_not_found(mock_services):
    _, mock_menu = mock_services
    mock_menu.delete_menu_item.return_value = False
    response = client.delete(f"/admin/restaurants/{RESTAURANT_ID}/menu/items/NonExistent")
    assert response.status_code == 404


def test_admin_delete_menu_item_any_restaurant(mock_services):
    response = client.delete("/admin/restaurants/99/menu/items/Burger")
    assert response.status_code == 204


# GET /admin/restaurants/{id}/profile

def test_admin_get_profile_200():
    response = client.get(f"/admin/restaurants/{RESTAURANT_ID}/profile")
    assert response.status_code == 200


def test_admin_get_profile_returns_data():
    data = client.get(f"/admin/restaurants/{RESTAURANT_ID}/profile").json()
    assert data["restaurant_id"] == RESTAURANT_ID
    assert data["name"] == "Restaurant_10"


def test_admin_get_profile_not_found(mock_services):
    mock_rest, _ = mock_services
    mock_rest.get_profile.return_value = None
    response = client.get("/admin/restaurants/999/profile")
    assert response.status_code == 404


# PUT /admin/restaurants/{id}/profile

def test_admin_update_profile_200():
    response = client.put(
        f"/admin/restaurants/{RESTAURANT_ID}/profile",
        json={"name": "New Name"},
    )
    assert response.status_code == 200


def test_admin_update_profile_any_restaurant(mock_services):
    response = client.put(
        "/admin/restaurants/99/profile",
        json={"name": "Updated"},
    )
    assert response.status_code == 200


def test_admin_update_profile_not_found(mock_services):
    mock_rest, _ = mock_services
    mock_rest.update_profile.return_value = None
    response = client.put(
        "/admin/restaurants/999/profile",
        json={"name": "Whatever"},
    )
    assert response.status_code == 404


def test_admin_update_profile_empty_name_422():
    response = client.put(
        f"/admin/restaurants/{RESTAURANT_ID}/profile",
        json={"name": ""},
    )
    assert response.status_code == 422


def test_admin_update_profile_whitespace_name_422():
    response = client.put(
        f"/admin/restaurants/{RESTAURANT_ID}/profile",
        json={"name": "   "},
    )
    assert response.status_code == 422


def test_admin_update_profile_no_auth_401():
    app.dependency_overrides.pop(get_current_admin, None)
    response = client.put(
        f"/admin/restaurants/{RESTAURANT_ID}/profile",
        json={"name": "Test"},
    )
    app.dependency_overrides[get_current_admin] = lambda: ADMIN_ID
    assert response.status_code == 401
