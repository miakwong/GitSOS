
import csv
import pytest
from unittest.mock import patch

from app.schemas.kaggle import KaggleRestaurant
import app.repositories.kaggle_restaurant_repository as repo

SAMPLE_ROWS = [
    {"restaurant_id": "10", "food_item": "Pasta",  "order_id": "A1", "order_value": "30.0",
     "customer_id": "abc", "order_time": "2024-01-01", "delivery_distance": "5.0",
     "delivery_time_actual": "1.0", "delivery_delay": "5.0"},
    {"restaurant_id": "10", "food_item": "Burger", "order_id": "A2", "order_value": "20.0",
     "customer_id": "abc", "order_time": "2024-01-02", "delivery_distance": "3.0",
     "delivery_time_actual": "0.5", "delivery_delay": "2.0"},
    {"restaurant_id": "20", "food_item": "Sushi",  "order_id": "A3", "order_value": "45.0",
     "customer_id": "def", "order_time": "2024-01-03", "delivery_distance": "7.0",
     "delivery_time_actual": "1.5", "delivery_delay": "8.0"},
]


@pytest.fixture(autouse=True)
def mock_csv(tmp_path):
    csv_file = tmp_path / "food_delivery.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SAMPLE_ROWS[0].keys())
        writer.writeheader()
        writer.writerows(SAMPLE_ROWS)
    with patch.object(repo, "CSV_PATH", str(csv_file)):
        yield


# list_all

def test_list_all_returns_unique_restaurants():
    # 3 rows but only 2 unique restaurant_ids
    results = repo.list_all()
    assert len(results) == 2


def test_list_all_returns_kaggle_restaurant_instances():
    assert all(isinstance(r, KaggleRestaurant) for r in repo.list_all())


def test_list_all_name_format():
    results = repo.list_all()
    for r in results:
        assert r.name == f"Restaurant_{r.restaurant_id}"


# get_by_id

def test_get_by_id_found():
    result = repo.get_by_id("10")
    assert result is not None
    assert result.restaurant_id == "10"
    assert result.name == "Restaurant_10"


def test_get_by_id_not_found():
    assert repo.get_by_id("999") is None


def test_get_by_id_returns_kaggle_restaurant_instance():
    result = repo.get_by_id("20")
    assert isinstance(result, KaggleRestaurant)