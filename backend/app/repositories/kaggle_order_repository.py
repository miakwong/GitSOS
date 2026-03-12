# repositories/kaggle_order_repository.py
# Read-only adapter for Kaggle food delivery CSV
# Never call any write operation on this data — DR1, DR2

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