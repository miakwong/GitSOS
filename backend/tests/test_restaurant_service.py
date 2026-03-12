from unittest.mock import patch

import app.services.restaurant_service as service
import pytest
from app.schemas.kaggle import KaggleMenuItem, KaggleRestaurant

RESTAURANTS = [
    KaggleRestaurant(restaurant_id="10", name="Restaurant_10"),
    KaggleRestaurant(restaurant_id="20", name="Restaurant_20"),
]

MENU_ITEMS = [
    KaggleMenuItem(restaurant_id="10", food_item="Pasta", median_price=35.0),
    KaggleMenuItem(restaurant_id="10", food_item="Burger", median_price=20.0),
]


@pytest.fixture(autouse=True)
def mock_repos():
    with patch(
        "app.services.restaurant_service.kaggle_restaurant_repository"
    ) as mock_rest, patch(
        "app.services.restaurant_service.kaggle_menu_repository"
    ) as mock_menu:
        mock_rest.list_all.return_value = RESTAURANTS
        mock_rest.get_by_id.side_effect = lambda rid: next(
            (r for r in RESTAURANTS if r.restaurant_id == rid), None
        )
        mock_menu.get_by_restaurant.side_effect = lambda rid: [
            m for m in MENU_ITEMS if m.restaurant_id == rid
        ]
        mock_menu.get_median_price.side_effect = lambda item: next(
            (m.median_price for m in MENU_ITEMS if m.food_item == item), None
        )
        yield


# list_restaurants


def test_list_restaurants_returns_all():
    results = service.list_restaurants()
    assert len(results) == 2


def test_list_restaurants_returns_kaggle_restaurant_instances():
    assert all(isinstance(r, KaggleRestaurant) for r in service.list_restaurants())


# get_restaurant


def test_get_restaurant_found():
    result = service.get_restaurant("10")
    assert result is not None
    assert result.restaurant_id == "10"


def test_get_restaurant_not_found():
    assert service.get_restaurant("999") is None


# get_menu


def test_get_menu_returns_items():
    results = service.get_menu("10")
    assert len(results) == 2


def test_get_menu_empty_for_unknown_restaurant():
    assert service.get_menu("999") == []


def test_get_menu_returns_kaggle_menu_item_instances():
    assert all(isinstance(m, KaggleMenuItem) for m in service.get_menu("10"))


# get_median_price


def test_get_median_price_known_item():
    assert service.get_median_price("Pasta") == 35.0


def test_get_median_price_unknown_item():
    assert service.get_median_price("Pizza") is None
