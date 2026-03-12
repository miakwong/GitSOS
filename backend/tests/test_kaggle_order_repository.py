
import csv
import os
import pytest
from unittest.mock import patch

from app.schemas.kaggle import KaggleOrder
import app.repositories.kaggle_order_repository as repo

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
        "age": "25", "gender": "Male", "location": "City_1",
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
        "age": "30", "gender": "Female", "location": "City_2",
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