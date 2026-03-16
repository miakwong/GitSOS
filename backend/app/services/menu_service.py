from typing import Optional

from app.repositories import kaggle_restaurant_repository, menu_repository
from app.schemas.menu import MenuItemCreate, MenuItemOut, MenuItemUpdate
from fastapi import HTTPException


def get_menu_items(restaurant_id: str) -> list[MenuItemOut]:
    return menu_repository.get_by_restaurant(restaurant_id)


def create_menu_item(restaurant_id: str, data: MenuItemCreate) -> MenuItemOut:
    if kaggle_restaurant_repository.get_by_id(restaurant_id) is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    existing = menu_repository.get_by_restaurant_and_food(restaurant_id, data.food_item)
    if existing:
        raise HTTPException(status_code=409, detail="Menu item already exists")
    return menu_repository.create(restaurant_id, data)


def update_menu_item(restaurant_id: str, food_item: str, data: MenuItemUpdate) -> Optional[MenuItemOut]:
    return menu_repository.update(restaurant_id, food_item, data)


def delete_menu_item(restaurant_id: str, food_item: str) -> bool:
    return menu_repository.delete(restaurant_id, food_item)
