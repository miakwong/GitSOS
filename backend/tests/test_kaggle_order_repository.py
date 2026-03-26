import csv
from unittest.mock import patch

import app.repositories.kaggle_order_repository as repo
import pytest
from app.schemas.kaggle import KaggleOrder

# Minimal fixture CSV rows
SAMPLE_ROWS = [
    {
        "order_id": "AAA001",
        "restaurant_id": "10",
        "customer_id": "abc-123",
        "food_item": "Pasta",
        "order_value": "30.0",
        "order_time": "2024-01-01",
        "delivery_distance": "5.0",
        "delivery_time_actual": "1.0",
        "delivery_delay": "5.0",
        "age": "25",
        "gender": "Male",
        "location": "City_1",
    },
    {
        "order_id": "BBB002",
        "restaurant_id": "20",
        "customer_id": "def-456",
        "food_item": "Burger",
        "order_value": "20.0",
        "order_time": "2024-02-01",
        "delivery_distance": "3.0",
        "delivery_time_actual": "0.5",
        "delivery_delay": "2.0",
        "age": "30",
        "gender": "Female",
        "location": "City_2",
    },
]


@pytest.fixture(autouse=True)
def mock_csv(tmp_path):
    """Write fixture CSV to tmp file and redirect CSV_PATH."""
    csv_file = tmp_path / "food_delivery.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SAMPLE_ROWS[0].keys())
        writer.writeheader()
        writer.writerows(SAMPLE_ROWS)
    with patch.object(repo, "CSV_PATH", str(csv_file)):
        yield


# load_all


def test_load_all_returns_list():
    results = repo.load_all()
    assert isinstance(results, list)


def test_load_all_count():
    assert len(repo.load_all()) == 2


def test_load_all_returns_kaggle_order_instances():
    assert all(isinstance(o, KaggleOrder) for o in repo.load_all())


def test_load_all_fields_mapped_correctly():
    orders = repo.load_all()
    assert orders[0].order_id == "AAA001"
    assert orders[0].food_item == "Pasta"
    assert orders[0].order_value == 30.0


# get_by_id


def test_get_by_id_found():
    result = repo.get_by_id("AAA001")
    assert result is not None
    assert result.order_id == "AAA001"


def test_get_by_id_not_found():
    assert repo.get_by_id("NOTEXIST") is None


def test_get_by_id_returns_correct_record():
    result = repo.get_by_id("BBB002")
    assert result.restaurant_id == "20"
    assert result.food_item == "Burger"


# get_by_customer_id


def test_get_by_customer_id_found():
    results = repo.get_by_customer_id("abc-123")
    assert len(results) == 1
    assert results[0].customer_id == "abc-123"


def test_get_by_customer_id_not_found():
    assert repo.get_by_customer_id("unknown") == []


def test_get_by_customer_id_returns_kaggle_order_instances():
    results = repo.get_by_customer_id("abc-123")
    assert all(isinstance(o, KaggleOrder) for o in results)


# get_by_food_item


def test_get_by_food_item_found():
    results = repo.get_by_food_item("Pasta")
    assert len(results) == 1
    assert results[0].food_item == "Pasta"


def test_get_by_food_item_not_found():
    assert repo.get_by_food_item("Pizza") == []


def test_get_by_food_item_multiple_results():
    results = repo.get_by_food_item("Burger")
    assert all(o.food_item == "Burger" for o in results)


# ------------------------------------------------------------------ #
# get_median_price — Three-tier fallback
# ------------------------------------------------------------------ #
# The mock_csv fixture gives us two rows:
#   restaurant_id = 10, food_item = "Pasta",  order_value = 30.0
#   restaurant_id = 20, food_item = "Burger", order_value = 20.0


def test_get_median_price_level1_exact_match():
    """Lv. 1: exact restaurant_id, food_item combo found -> return its median."""
    result = repo.get_median_price(10, "Pasta")
    assert result == 30.0


def test_get_median_price_level2_global_fallback():
    """
    Lv. 2: food_item exists globally but NOT at the given restaurant.
    restaurant_id = 99 has no Pasta, but Pasta exists at restaurant 10.
    """
    result = repo.get_median_price(99, "Pasta")
    assert result == 30.0


def test_get_median_price_level3_default_price():
    """Lv. 3: food_item not in Kaggle at all -> return $25.00 default."""
    result = repo.get_median_price(99, "UnknownDish")
    assert result == 25.00


def test_get_median_price_uses_median_not_average():
    """
    When there are multiple prices for the same combo, the function
    should return the MEDIAN, not the average.
    Prices: [10.0, 20.0, 50.0] -> median = 20.0, average = 26.67
    """
    rows = [
        {
            "order_id": "X1", "restaurant_id": "5", "food_item": "Sushi",
            "order_value": "10.0", "order_time": "2024-01-01",
            "customer_id": "c1", "delivery_distance": "3.0",
            "delivery_time_actual": "1.0", "delivery_delay": "0.0",
        },
        {
            "order_id": "X2", "restaurant_id": "5", "food_item": "Sushi",
            "order_value": "20.0", "order_time": "2024-01-01",
            "customer_id": "c2", "delivery_distance": "3.0",
            "delivery_time_actual": "1.0", "delivery_delay": "0.0",
        },
        {
            "order_id": "X3", "restaurant_id": "5", "food_item": "Sushi",
            "order_value": "50.0", "order_time": "2024-01-01",
            "customer_id": "c3", "delivery_distance": "3.0",
            "delivery_time_actual": "1.0", "delivery_delay": "0.0",
        },
    ]
    with patch.object(repo, "_load_csv", return_value=rows):
        result = repo.get_median_price(5, "Sushi")

    assert result == 20.0   # median, not average = 26.67


def test_get_median_price_level2_uses_global_median():
    """
    Lv. 2 global fallback should also use the MEDIAN across all restaurants.
    Same food_item at two different restaurants: [10.0, 40.0] -> median = 25.0
    """
    rows = [
        {
            "order_id": "Y1", "restaurant_id": "1", "food_item": "Tacos",
            "order_value": "10.0", "order_time": "2024-01-01",
            "customer_id": "c1", "delivery_distance": "3.0",
            "delivery_time_actual": "1.0", "delivery_delay": "0.0",
        },
        {
            "order_id": "Y2", "restaurant_id": "2", "food_item": "Tacos",
            "order_value": "40.0", "order_time": "2024-01-01",
            "customer_id": "c2", "delivery_distance": "3.0",
            "delivery_time_actual": "1.0", "delivery_delay": "0.0",
        },
    ]
    with patch.object(repo, "_load_csv", return_value=rows):
        # restaurant_id = 99 not in data -> falls back to global Tacos median
        result = repo.get_median_price(99, "Tacos")

    assert result == 25.0  # median of [10.0, 40.0]
