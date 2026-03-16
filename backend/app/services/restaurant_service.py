from typing import Optional

from app.repositories import kaggle_menu_repository, kaggle_restaurant_repository
from app.schemas.kaggle import KaggleMenuItem, KaggleRestaurant


def list_restaurants() -> list[KaggleRestaurant]:
    # Return all unique restaurants from the dataset
    return kaggle_restaurant_repository.list_all()


def get_restaurant(restaurant_id: str) -> Optional[KaggleRestaurant]:
    # Return a single restaurant by ID or None
    return kaggle_restaurant_repository.get_by_id(restaurant_id)


def get_menu_for_restaurant(restaurant_id: str) -> Optional[list[KaggleMenuItem]]:
    # returns None if the restaurant doesn't exist
    # returns a list (possibly empty) if the restaurant exists
    if kaggle_restaurant_repository.get_by_id(restaurant_id) is None:
        return None
    return kaggle_menu_repository.get_by_restaurant(restaurant_id)


def get_median_price(food_item: str) -> Optional[float]:
    # Return the median order_value for a food item 
    # Used by pricing_service to compute order subtotal.
    return kaggle_menu_repository.get_median_price(food_item)
