from unittest.mock import patch

import app.repositories.menu_repository as repo
import pytest
from app.schemas.menu import MenuItemCreate, MenuItemUpdate


@pytest.fixture(autouse=True)
def tmp_store(tmp_path):
    json_file = tmp_path / "menu_items.json"
    json_file.write_text("[]")
    with patch.object(repo, "DATA_PATH", str(json_file)):
        yield


def test_create_stores_item():
    result = repo.create("16", MenuItemCreate(food_item="Burger", price=12.50))
    assert result.food_item == "Burger"
    assert result.price == 12.50
    assert result.restaurant_id == "16"


def test_create_persists_to_file():
    repo.create("16", MenuItemCreate(food_item="Burger", price=12.50))
    results = repo.get_by_restaurant("16")
    assert len(results) == 1


def test_get_by_restaurant_returns_all_items():
    repo.create("16", MenuItemCreate(food_item="Burger", price=12.50))
    repo.create("16", MenuItemCreate(food_item="Fries", price=5.0))
    results = repo.get_by_restaurant("16")
    assert len(results) == 2


def test_get_by_restaurant_filters_by_id():
    repo.create("16", MenuItemCreate(food_item="Burger", price=12.50))
    repo.create("30", MenuItemCreate(food_item="Pasta", price=15.0))
    results = repo.get_by_restaurant("16")
    assert len(results) == 1
    assert results[0].food_item == "Burger"


def test_get_by_restaurant_empty_when_none():
    assert repo.get_by_restaurant("999") == []


def test_get_by_restaurant_and_food_found():
    repo.create("16", MenuItemCreate(food_item="Burger", price=12.50))
    result = repo.get_by_restaurant_and_food("16", "Burger")
    assert result is not None
    assert result.food_item == "Burger"


def test_get_by_restaurant_and_food_not_found():
    assert repo.get_by_restaurant_and_food("16", "Pizza") is None


def test_get_by_restaurant_and_food_wrong_restaurant():
    repo.create("16", MenuItemCreate(food_item="Burger", price=12.50))
    assert repo.get_by_restaurant_and_food("30", "Burger") is None


def test_update_changes_price():
    repo.create("16", MenuItemCreate(food_item="Burger", price=12.50))
    result = repo.update("16", "Burger", MenuItemUpdate(price=15.0))
    assert result is not None
    assert result.price == 15.0


def test_update_changes_food_item():
    repo.create("16", MenuItemCreate(food_item="Burger", price=12.50))
    result = repo.update("16", "Burger", MenuItemUpdate(food_item="Big Burger"))
    assert result is not None
    assert result.food_item == "Big Burger"


def test_update_not_found_returns_none():
    result = repo.update("16", "NonExistent", MenuItemUpdate(price=10.0))
    assert result is None


def test_update_persists_changes():
    repo.create("16", MenuItemCreate(food_item="Burger", price=12.50))
    repo.update("16", "Burger", MenuItemUpdate(price=20.0))
    result = repo.get_by_restaurant_and_food("16", "Burger")
    assert result.price == 20.0


def test_delete_removes_item():
    repo.create("16", MenuItemCreate(food_item="Burger", price=12.50))
    found = repo.delete("16", "Burger")
    assert found is True
    assert repo.get_by_restaurant("16") == []


def test_delete_not_found_returns_false():
    assert repo.delete("16", "NonExistent") is False


def test_delete_only_removes_matching_item():
    repo.create("16", MenuItemCreate(food_item="Burger", price=12.50))
    repo.create("16", MenuItemCreate(food_item="Fries", price=5.0))
    repo.delete("16", "Burger")
    remaining = repo.get_by_restaurant("16")
    assert len(remaining) == 1
    assert remaining[0].food_item == "Fries"
