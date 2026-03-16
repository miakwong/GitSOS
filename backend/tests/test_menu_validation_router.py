from unittest.mock import patch
from uuid import uuid4

import pytest
from app.dependencies import get_current_owner
from app.main import app
from app.schemas.menu import MenuItemOut
from fastapi.testclient import TestClient

client = TestClient(app)

OWNER_ID = uuid4()
RESTAURANT_ID = "16"
OWNER_RESTAURANT_INT = 16

ITEM = MenuItemOut(restaurant_id=RESTAURANT_ID, food_item="Burger", price=12.50)


@pytest.fixture(autouse=True)
def mock_owner():
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, OWNER_RESTAURANT_INT)
    yield
    app.dependency_overrides.pop(get_current_owner, None)


@pytest.fixture(autouse=True)
def mock_menu_svc():
    with patch("app.routers.restaurants.menu_service") as mock:
        mock.get_menu_items.return_value = [ITEM]
        mock.create_menu_item.return_value = ITEM
        mock.update_menu_item.return_value = ITEM
        mock.delete_menu_item.return_value = True
        yield mock


# GET /restaurants/{id}/menu/items

def test_list_owner_menu_items_200():
    response = client.get(f"/restaurants/{RESTAURANT_ID}/menu/items")
    assert response.status_code == 200


def test_list_owner_menu_items_returns_list():
    data = client.get(f"/restaurants/{RESTAURANT_ID}/menu/items").json()
    assert isinstance(data, list)
    assert data[0]["food_item"] == "Burger"
    assert data[0]["price"] == 12.50


# POST /restaurants/{id}/menu/items

def test_add_menu_item_201():
    response = client.post(
        f"/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "Burger", "price": 12.50},
    )
    assert response.status_code == 201


def test_add_menu_item_returns_item():
    data = client.post(
        f"/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "Burger", "price": 12.50},
    ).json()
    assert data["food_item"] == "Burger"
    assert data["price"] == 12.50


def test_add_menu_item_missing_food_item_422():
    response = client.post(
        f"/restaurants/{RESTAURANT_ID}/menu/items",
        json={"price": 12.50},
    )
    assert response.status_code == 422


def test_add_menu_item_empty_food_item_422():
    response = client.post(
        f"/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "", "price": 12.50},
    )
    assert response.status_code == 422


def test_add_menu_item_whitespace_food_item_422():
    response = client.post(
        f"/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "   ", "price": 12.50},
    )
    assert response.status_code == 422


def test_add_menu_item_missing_price_422():
    response = client.post(
        f"/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "Burger"},
    )
    assert response.status_code == 422


def test_add_menu_item_zero_price_422():
    response = client.post(
        f"/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "Burger", "price": 0},
    )
    assert response.status_code == 422


def test_add_menu_item_negative_price_422():
    response = client.post(
        f"/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "Burger", "price": -5.0},
    )
    assert response.status_code == 422


def test_add_menu_item_wrong_restaurant_403():
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, 99)
    response = client.post(
        f"/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "Burger", "price": 12.50},
    )
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, OWNER_RESTAURANT_INT)
    assert response.status_code == 403


def test_add_menu_item_no_auth_401():
    app.dependency_overrides.pop(get_current_owner, None)
    response = client.post(
        f"/restaurants/{RESTAURANT_ID}/menu/items",
        json={"food_item": "Burger", "price": 12.50},
    )
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, OWNER_RESTAURANT_INT)
    assert response.status_code == 401


# PUT /restaurants/{id}/menu/items/{food_item}

def test_update_menu_item_200():
    response = client.put(
        f"/restaurants/{RESTAURANT_ID}/menu/items/Burger",
        json={"price": 15.0},
    )
    assert response.status_code == 200


def test_update_menu_item_not_found_404(mock_menu_svc):
    mock_menu_svc.update_menu_item.return_value = None
    response = client.put(
        f"/restaurants/{RESTAURANT_ID}/menu/items/NonExistent",
        json={"price": 15.0},
    )
    assert response.status_code == 404


def test_update_menu_item_negative_price_422():
    response = client.put(
        f"/restaurants/{RESTAURANT_ID}/menu/items/Burger",
        json={"price": -1.0},
    )
    assert response.status_code == 422


def test_update_menu_item_zero_price_422():
    response = client.put(
        f"/restaurants/{RESTAURANT_ID}/menu/items/Burger",
        json={"price": 0},
    )
    assert response.status_code == 422


def test_update_menu_item_empty_food_item_422():
    response = client.put(
        f"/restaurants/{RESTAURANT_ID}/menu/items/Burger",
        json={"food_item": ""},
    )
    assert response.status_code == 422


def test_update_menu_item_wrong_restaurant_403():
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, 99)
    response = client.put(
        f"/restaurants/{RESTAURANT_ID}/menu/items/Burger",
        json={"price": 15.0},
    )
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, OWNER_RESTAURANT_INT)
    assert response.status_code == 403


# DELETE /restaurants/{id}/menu/items/{food_item}

def test_delete_menu_item_204():
    response = client.delete(f"/restaurants/{RESTAURANT_ID}/menu/items/Burger")
    assert response.status_code == 204


def test_delete_menu_item_not_found_404(mock_menu_svc):
    mock_menu_svc.delete_menu_item.return_value = False
    response = client.delete(f"/restaurants/{RESTAURANT_ID}/menu/items/NonExistent")
    assert response.status_code == 404


def test_delete_menu_item_wrong_restaurant_403():
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, 99)
    response = client.delete(f"/restaurants/{RESTAURANT_ID}/menu/items/Burger")
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, OWNER_RESTAURANT_INT)
    assert response.status_code == 403


def test_delete_menu_item_no_auth_401():
    app.dependency_overrides.pop(get_current_owner, None)
    response = client.delete(f"/restaurants/{RESTAURANT_ID}/menu/items/Burger")
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, OWNER_RESTAURANT_INT)
    assert response.status_code == 401
