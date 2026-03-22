import pytest
from fastapi import HTTPException

from app.services.sort_helper import (
    VALID_MENU_ITEM_SORT_KEYS,
    VALID_ORDER_SORT_KEYS,
    VALID_RESTAURANT_SORT_KEYS,
    sort_results,
)

# ------------------------------------------------------------------
# Shared sample data used across tests
# ------------------------------------------------------------------
RESTAURANTS = [
    {"restaurant_id": "R3", "restaurant_name": "Sushi House"},
    {"restaurant_id": "R1", "restaurant_name": "Burger Town"},
    {"restaurant_id": "R2", "restaurant_name": "Pizza Place"},
]

MENU_ITEMS = [
    {"item_name": "Pizza",  "price": 15.0},
    {"item_name": "Burger", "price": 8.0},
    {"item_name": "Sushi",  "price": 22.0},
]

ORDERS = [
    {"order_id": "O3", "order_value": 30.0},
    {"order_id": "O1", "order_value": 10.0},
    {"order_id": "O2", "order_value": 20.0},
]


# ------------------------------------------------------------------
# No sorting requested
# ------------------------------------------------------------------
def test_no_sort_returns_list_unchanged():
    # When sort_by is None, the original order should be kept
    result = sort_results(RESTAURANTS, sort_by=None, sort_order="asc", valid_sort_keys=VALID_RESTAURANT_SORT_KEYS)
    assert result == RESTAURANTS


# ------------------------------------------------------------------
# Sort restaurants by name
# ------------------------------------------------------------------
def test_sort_restaurants_by_name_asc():
    result = sort_results(RESTAURANTS, sort_by="restaurant_name", sort_order="asc", valid_sort_keys=VALID_RESTAURANT_SORT_KEYS)
    names = [r["restaurant_name"] for r in result]
    assert names == ["Burger Town", "Pizza Place", "Sushi House"]


def test_sort_restaurants_by_name_desc():
    result = sort_results(RESTAURANTS, sort_by="restaurant_name", sort_order="desc", valid_sort_keys=VALID_RESTAURANT_SORT_KEYS)
    names = [r["restaurant_name"] for r in result]
    assert names == ["Sushi House", "Pizza Place", "Burger Town"]


def test_sort_restaurants_by_id_asc():
    result = sort_results(RESTAURANTS, sort_by="restaurant_id", sort_order="asc", valid_sort_keys=VALID_RESTAURANT_SORT_KEYS)
    ids = [r["restaurant_id"] for r in result]
    assert ids == ["R1", "R2", "R3"]


# ------------------------------------------------------------------
# Sort menu items by price
# ------------------------------------------------------------------
def test_sort_menu_items_by_price_asc():
    result = sort_results(MENU_ITEMS, sort_by="price", sort_order="asc", valid_sort_keys=VALID_MENU_ITEM_SORT_KEYS)
    prices = [r["price"] for r in result]
    assert prices == [8.0, 15.0, 22.0]


def test_sort_menu_items_by_price_desc():
    result = sort_results(MENU_ITEMS, sort_by="price", sort_order="desc", valid_sort_keys=VALID_MENU_ITEM_SORT_KEYS)
    prices = [r["price"] for r in result]
    assert prices == [22.0, 15.0, 8.0]


def test_sort_menu_items_by_name_asc():
    result = sort_results(MENU_ITEMS, sort_by="item_name", sort_order="asc", valid_sort_keys=VALID_MENU_ITEM_SORT_KEYS)
    names = [r["item_name"] for r in result]
    assert names == ["Burger", "Pizza", "Sushi"]


# ------------------------------------------------------------------
# Sort orders by order_value
# ------------------------------------------------------------------
def test_sort_orders_by_value_asc():
    result = sort_results(ORDERS, sort_by="order_value", sort_order="asc", valid_sort_keys=VALID_ORDER_SORT_KEYS)
    values = [r["order_value"] for r in result]
    assert values == [10.0, 20.0, 30.0]


def test_sort_orders_by_value_desc():
    result = sort_results(ORDERS, sort_by="order_value", sort_order="desc", valid_sort_keys=VALID_ORDER_SORT_KEYS)
    values = [r["order_value"] for r in result]
    assert values == [30.0, 20.0, 10.0]


# ------------------------------------------------------------------
# Invalid sort_by raises 400
# ------------------------------------------------------------------
def test_invalid_sort_by_raises_400():
    # "city" is not a valid sort key for restaurants
    with pytest.raises(HTTPException) as exc_info:
        sort_results(RESTAURANTS, sort_by="city", sort_order="asc", valid_sort_keys=VALID_RESTAURANT_SORT_KEYS)

    assert exc_info.value.status_code == 400
    assert "city" in exc_info.value.detail["message"]


def test_invalid_sort_by_shows_allowed_keys():
    with pytest.raises(HTTPException) as exc_info:
        sort_results(MENU_ITEMS, sort_by="category", sort_order="asc", valid_sort_keys=VALID_MENU_ITEM_SORT_KEYS)

    assert "allowed_sort_keys" in exc_info.value.detail


# ------------------------------------------------------------------
# Rows missing the sort field go to the end
# ------------------------------------------------------------------
def test_missing_field_goes_to_end():
    rows = [
        {"restaurant_name": "Sushi House"},
        {"restaurant_name": None},          # missing value
        {"restaurant_name": "Burger Town"},
    ]
    result = sort_results(rows, sort_by="restaurant_name", sort_order="asc", valid_sort_keys=VALID_RESTAURANT_SORT_KEYS)
    names = [r["restaurant_name"] for r in result]
    # None should always be last
    assert names == ["Burger Town", "Sushi House", None]


# ------------------------------------------------------------------
# Empty list returns empty list
# ------------------------------------------------------------------
def test_empty_list_returns_empty():
    result = sort_results([], sort_by="restaurant_name", sort_order="asc", valid_sort_keys=VALID_RESTAURANT_SORT_KEYS)
    assert result == []
