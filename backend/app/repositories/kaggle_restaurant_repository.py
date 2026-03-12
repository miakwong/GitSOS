# repositories/kaggle_restaurant_repository.py
# Read-only — extracts unique restaurants from Kaggle CSV
# restaurant_id is str (numeric e.g. "16")

import csv
import os
from typing import Optional

from app.schemas.kaggle import KaggleRestaurant

CSV_PATH = os.path.join(os.path.dirname(__file__), "../data/food_delivery.csv")


def _load_csv() -> list[dict]:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def list_all() -> list[KaggleRestaurant]:
    seen = set()
    restaurants = []
    for row in _load_csv():
        rid = row["restaurant_id"]
        if rid not in seen:
            seen.add(rid)
            restaurants.append(KaggleRestaurant(
                restaurant_id=rid,
                name=f"Restaurant_{rid}",
            ))
    return restaurants


def get_by_id(restaurant_id: str) -> Optional[KaggleRestaurant]:
    for row in _load_csv():
        if row["restaurant_id"] == restaurant_id:
            return KaggleRestaurant(
                restaurant_id=restaurant_id,
                name=f"Restaurant_{restaurant_id}",
            )
    return None