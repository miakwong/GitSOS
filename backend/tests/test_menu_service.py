from unittest.mock import patch

import app.services.menu_service as service
import pytest
from app.schemas.menu import MenuItemCreate, MenuItemOut, MenuItemUpdate
from fastapi import HTTPException

ITEM = MenuItemOut(restaurant_id="16", food_item="Burger", price=12.50)


@pytest.fixture(autouse=True)
def mock_repo():
    with patch("app.services.menu_service.menu_repository") as mock:
        mock.get_by_restaurant.return_value = [ITEM]
        mock.get_by_restaurant_and_food.return_value = None
        mock.create.return_value = ITEM
        mock.update.return_value = ITEM
        mock.delete.return_value = True
        yield mock


def test_get_menu_items_returns_list(mock_repo):
    results = service.get_menu_items("16")
    assert len(results) == 1
    assert results[0].food_item == "Burger"


def test_get_menu_items_calls_repo(mock_repo):
    service.get_menu_items("16")
    mock_repo.get_by_restaurant.assert_called_once_with("16")


def test_create_menu_item_success(mock_repo):
    data = MenuItemCreate(food_item="Burger", price=12.50)
    result = service.create_menu_item("16", data)
    assert result.food_item == "Burger"
    mock_repo.create.assert_called_once()


def test_create_menu_item_duplicate_raises_409(mock_repo):
    mock_repo.get_by_restaurant_and_food.return_value = ITEM
    data = MenuItemCreate(food_item="Burger", price=12.50)
    with pytest.raises(HTTPException) as exc:
        service.create_menu_item("16", data)
    assert exc.value.status_code == 409


def test_create_menu_item_checks_for_duplicate(mock_repo):
    data = MenuItemCreate(food_item="Burger", price=12.50)
    service.create_menu_item("16", data)
    mock_repo.get_by_restaurant_and_food.assert_called_once_with("16", "Burger")


def test_update_menu_item_success(mock_repo):
    data = MenuItemUpdate(price=15.0)
    result = service.update_menu_item("16", "Burger", data)
    assert result is not None
    mock_repo.update.assert_called_once_with("16", "Burger", data)


def test_update_menu_item_not_found_returns_none(mock_repo):
    mock_repo.update.return_value = None
    result = service.update_menu_item("16", "NonExistent", MenuItemUpdate(price=10.0))
    assert result is None


def test_delete_menu_item_success(mock_repo):
    found = service.delete_menu_item("16", "Burger")
    assert found is True
    mock_repo.delete.assert_called_once_with("16", "Burger")


def test_delete_menu_item_not_found(mock_repo):
    mock_repo.delete.return_value = False
    found = service.delete_menu_item("16", "NonExistent")
    assert found is False
