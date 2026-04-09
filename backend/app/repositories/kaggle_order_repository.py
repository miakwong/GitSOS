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


def _median(prices: list[float]) -> float:
    n = len(prices)
    mid = n // 2
    if n % 2 == 0:
        return (prices[mid - 1] + prices[mid]) / 2
    return prices[mid]


def get_median_price(restaurant_id: int, food_item: str) -> float:
    """Three-tier price fallback:
    1. Median price for this food_item at this restaurant.
    2. Global median for this food_item across all restaurants.
    3. Default $25.00 if food_item not in Kaggle at all.
    """
    rows = _load_csv()

    # Tier 1: exact restaurant + food_item match
    exact = sorted(
        float(r["order_value"])
        for r in rows
        if r.get("food_item") == food_item and r.get("restaurant_id") == str(restaurant_id)
    )
    if exact:
        return _median(exact)

    # Tier 2: global food_item median
    global_prices = sorted(
        float(r["order_value"]) for r in rows if r.get("food_item") == food_item
    )
    if global_prices:
        return _median(global_prices)

    # Tier 3: default
    return 25.00
