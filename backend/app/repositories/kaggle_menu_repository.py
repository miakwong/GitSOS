# repositories/kaggle_menu_repository.py
# Read-only — extracts menu items from Kaggle CSV
# median_price precomputed once at module load from all order_value entries per food_item

import csv
import os
from statistics import median
from typing import Optional

from app.schemas.kaggle import KaggleMenuItem

CSV_PATH = os.path.join(os.path.dirname(__file__), "../data/food_delivery.csv")


def _load_csv() -> list[dict]:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _compute_median_prices() -> dict[str, float]:
    prices: dict[str, list[float]] = {}
    for row in _load_csv():
        item = row["food_item"]
        prices.setdefault(item, []).append(float(row["order_value"]))
    return {item: median(vals) for item, vals in prices.items()}


# Precomputed once at import time
_MEDIAN_PRICES: dict[str, float] = _compute_median_prices()


def list_all() -> list[KaggleMenuItem]:
    seen = set()
    items = []
    for row in _load_csv():
        key = (row["restaurant_id"], row["food_item"])
        if key not in seen:
            seen.add(key)
            items.append(
                KaggleMenuItem(
                    restaurant_id=row["restaurant_id"],
                    food_item=row["food_item"],
                    median_price=_MEDIAN_PRICES.get(row["food_item"], 0.0),
                )
            )
    return items


def get_by_restaurant(restaurant_id: str) -> list[KaggleMenuItem]:
    seen = set()
    items = []
    for row in _load_csv():
        if row["restaurant_id"] == restaurant_id and row["food_item"] not in seen:
            seen.add(row["food_item"])
            items.append(
                KaggleMenuItem(
                    restaurant_id=restaurant_id,
                    food_item=row["food_item"],
                    median_price=_MEDIAN_PRICES.get(row["food_item"], 0.0),
                )
            )
    return items


def get_median_price(food_item: str) -> Optional[float]:
    return _MEDIAN_PRICES.get(food_item)
