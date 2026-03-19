import json
import os
from typing import Optional

from app.schemas.menu import MenuItemCreate, MenuItemOut, MenuItemUpdate

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/menu_items.json")


def _load() -> list[dict]:
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(items: list[dict]) -> None:
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)


def get_by_restaurant(restaurant_id: str) -> list[MenuItemOut]:
    return [MenuItemOut(**item) for item in _load() if item["restaurant_id"] == restaurant_id]


def get_by_restaurant_and_food(restaurant_id: str, food_item: str) -> Optional[MenuItemOut]:
    for item in _load():
        if item["restaurant_id"] == restaurant_id and item["food_item"] == food_item:
            return MenuItemOut(**item)
    return None


def create(restaurant_id: str, data: MenuItemCreate) -> MenuItemOut:
    items = _load()
    new_item = {
        "restaurant_id": restaurant_id,
        "food_item": data.food_item,
        "price": data.price,
    }
    items.append(new_item)
    _save(items)
    return MenuItemOut(**new_item)


def update(restaurant_id: str, food_item: str, data: MenuItemUpdate) -> Optional[MenuItemOut]:
    items = _load()
    for item in items:
        if item["restaurant_id"] == restaurant_id and item["food_item"] == food_item:
            if data.food_item is not None:
                item["food_item"] = data.food_item
            if data.price is not None:
                item["price"] = data.price
            _save(items)
            return MenuItemOut(**item)
    return None


def delete(restaurant_id: str, food_item: str) -> bool:
    items = _load()
    filtered = [
        i for i in items
        if not (i["restaurant_id"] == restaurant_id and i["food_item"] == food_item)
    ]
    if len(filtered) == len(items):
        return False
    _save(filtered)
    return True
