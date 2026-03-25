import csv
import os
import statistics
from typing import Optional

from app.schemas.kaggle import KaggleOrder

CSV_PATH = os.path.join(os.path.dirname(__file__), "../data/food_delivery.csv")

# Default food price when item is not found in Kaggle data at all
DEFAULT_FOOD_PRICE = 25.00


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


def get_median_price(restaurant_id: int, food_item: str) -> float:
    """
    Get the food base price using a 3-tier fallback strategy:

    Level 1 Primary: Median order_value for this exact restaurant_id, food_item pair
    Level 2 Fallback: Global median order_value for food_item across ALL restaurants
    Level 3 Default:  $25.00 if the food item is not found anywhere in Kaggle data
    """
    rows = _load_csv()

    # --- Lv. 1: Look for prices from this specific restaurant + food item ---
    specific_prices = [
        float(row["order_value"])
        for row in rows
        if str(row["restaurant_id"]) == str(restaurant_id) and row["food_item"] == food_item
    ]

    if specific_prices:
        return round(statistics.median(specific_prices), 2)

    # --- Lv. 2: Look for prices of this food item across ALL restaurants ---
    global_prices = [
        float(row["order_value"])
        for row in rows
        if row["food_item"] == food_item
    ]

    if global_prices:
        return round(statistics.median(global_prices), 2)

    # --- Lv. 3: Food item not in Kaggle at all, use default price ---
    return DEFAULT_FOOD_PRICE
