from unittest.mock import patch

import app.services.restaurant_service as service
import pytest
from app.schemas.kaggle import KaggleMenuItem

ITEMS = [
    KaggleMenuItem(restaurant_id="10", food_item="Beef Burger", median_price=12.0),
    KaggleMenuItem(restaurant_id="10", food_item="Veggie Burger", median_price=10.0),
    KaggleMenuItem(restaurant_id="20", food_item="Pasta Carbonara", median_price=15.0),
    KaggleMenuItem(restaurant_id="20", food_item="Garlic Bread", median_price=5.0),
]


@pytest.fixture(autouse=True)
def mock_menu_repo():
    with patch("app.services.restaurant_service.kaggle_menu_repository") as mock:
        mock.list_all.return_value = ITEMS
        yield mock


def test_search_menu_returns_matching_items():
    results = service.search_menu("Burger")
    assert len(results) == 2


def test_search_menu_case_insensitive():
    results = service.search_menu("burger")
    assert len(results) == 2


def test_search_menu_partial_match():
    results = service.search_menu("Pasta")
    assert len(results) == 1
    assert results[0].food_item == "Pasta Carbonara"


def test_search_menu_no_match_returns_empty():
    results = service.search_menu("Sushi")
    assert results == []


def test_search_menu_excludes_unrelated():
    results = service.search_menu("Bread")
    assert len(results) == 1
    assert results[0].food_item == "Garlic Bread"


def test_search_menu_calls_list_all(mock_menu_repo):
    service.search_menu("Burger")
    mock_menu_repo.list_all.assert_called_once()


def test_search_menu_returns_kaggle_menu_item_instances():
    results = service.search_menu("Burger")
    assert all(isinstance(r, KaggleMenuItem) for r in results)


def test_search_menu_strips_whitespace():
    results = service.search_menu("  Burger  ")
    assert len(results) == 2
