import csv
from statistics import median
from unittest.mock import patch

import app.repositories.kaggle_menu_repository as repo
import pytest
from app.schemas.kaggle import KaggleMenuItem

SAMPLE_ROWS = [
    {
        "restaurant_id": "10",
        "food_item": "Pasta",
        "order_id": "A1",
        "order_value": "30.0",
        "customer_id": "abc",
        "order_time": "2024-01-01",
        "delivery_distance": "5.0",
        "delivery_time_actual": "1.0",
        "delivery_delay": "5.0",
    },
    {
        "restaurant_id": "10",
        "food_item": "Pasta",
        "order_id": "A2",
        "order_value": "40.0",
        "customer_id": "abc",
        "order_time": "2024-01-02",
        "delivery_distance": "3.0",
        "delivery_time_actual": "0.5",
        "delivery_delay": "2.0",
    },
    {
        "restaurant_id": "10",
        "food_item": "Burger",
        "order_id": "A3",
        "order_value": "20.0",
        "customer_id": "def",
        "order_time": "2024-01-03",
        "delivery_distance": "7.0",
        "delivery_time_actual": "1.5",
        "delivery_delay": "8.0",
    },
    {
        "restaurant_id": "20",
        "food_item": "Sushi",
        "order_id": "A4",
        "order_value": "45.0",
        "customer_id": "ghi",
        "order_time": "2024-01-04",
        "delivery_distance": "2.0",
        "delivery_time_actual": "0.8",
        "delivery_delay": "1.0",
    },
]


@pytest.fixture(autouse=True)
def mock_csv(tmp_path):
    csv_file = tmp_path / "food_delivery.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SAMPLE_ROWS[0].keys())
        writer.writeheader()
        writer.writerows(SAMPLE_ROWS)
    with patch.object(repo, "CSV_PATH", str(csv_file)):
        # recompute median prices with fixture data
        repo._MEDIAN_PRICES = repo._compute_median_prices()
        yield


# list_all


def test_list_all_returns_unique_items():
    # 4 rows: Pasta x2 (same restaurant), Burger x1, Sushi x1 → 3 unique (rid, food_item)
    results = repo.list_all()
    assert len(results) == 3


def test_list_all_returns_kaggle_menu_item_instances():
    assert all(isinstance(m, KaggleMenuItem) for m in repo.list_all())


def test_list_all_median_price_correct():
    results = repo.list_all()
    pasta = next(m for m in results if m.food_item == "Pasta")
    assert pasta.median_price == median([30.0, 40.0])


# get_by_restaurant


def test_get_by_restaurant_found():
    results = repo.get_by_restaurant("10")
    assert len(results) == 2
    food_items = {m.food_item for m in results}
    assert food_items == {"Pasta", "Burger"}


def test_get_by_restaurant_not_found():
    assert repo.get_by_restaurant("999") == []


def test_get_by_restaurant_returns_kaggle_menu_item_instances():
    results = repo.get_by_restaurant("20")
    assert all(isinstance(m, KaggleMenuItem) for m in results)


# get_median_price


def test_get_median_price_known_item():
    price = repo.get_median_price("Pasta")
    assert price == median([30.0, 40.0])


def test_get_median_price_unknown_item():
    assert repo.get_median_price("Pizza") is None


def test_get_median_price_single_entry():
    assert repo.get_median_price("Sushi") == 45.0
