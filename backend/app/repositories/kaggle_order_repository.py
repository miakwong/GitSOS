# repositories/kaggle_order_repository.py
# Read-only adapter for Kaggle food delivery CSV

import csv
import os
from typing import Optional

from app.schemas.kaggle import KaggleOrder

CSV_PATH = os.path.join(os.path.dirname(__file__), "../data/food_delivery.csv")


def _load_csv() -> list[dict]:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_all() -> list[KaggleOrder]:
    return [_row_to_order(row) for row in _load_csv()]


def get_by_id(order_id: str) -> Optional[KaggleOrder]:
    for row in _load_csv():
        if row["order_id"] == order_id:
            return _row_to_order(row)
    return None


def _row_to_order(row: dict) -> KaggleOrder:
    return KaggleOrder(
        order_id=row["order_id"],
        restaurant_id=row["restaurant_id"],
        customer_id=row["customer_id"],
        food_item=row["food_item"],
        order_value=float(row["order_value"]),
        order_time=row["order_time"],
        delivery_distance=float(row["delivery_distance"]),
        delivery_time_actual=float(row["delivery_time_actual"]),
        delivery_delay=float(row["delivery_delay"]),
    )


def get_by_customer_id(customer_id: str) -> list[KaggleOrder]:
    return [
        _row_to_order(row) for row in _load_csv() if row["customer_id"] == customer_id
    ]


def get_by_food_item(food_item: str) -> list[KaggleOrder]:
    return [_row_to_order(row) for row in _load_csv() if row["food_item"] == food_item]


def get_median_price(food_item: str) -> Optional[float]:
    """Get median price for a food item from Kaggle historical data."""
    orders = get_by_food_item(food_item)
    if not orders:
        return None
    prices = sorted([o.order_value for o in orders])
    n = len(prices)
    mid = n // 2
    if n % 2 == 0:
        return (prices[mid - 1] + prices[mid]) / 2
    return prices[mid]
