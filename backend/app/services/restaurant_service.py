from typing import Optional

from app.repositories import kaggle_menu_repository, kaggle_restaurant_repository, restaurant_profile_repository
from app.schemas.kaggle import KaggleMenuItem, KaggleRestaurant
from app.schemas.restaurant_profile import RestaurantProfileOut, RestaurantProfileUpdate


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
    # Used by pricing_service to compute order subtotal
    return kaggle_menu_repository.get_median_price(food_item)


def get_profile(restaurant_id: str) -> Optional[RestaurantProfileOut]:
    # Returns owner-managed profile if it exists otherwise falls back to Kaggle data
    profile = restaurant_profile_repository.get_by_id(restaurant_id)
    if profile:
        return profile
    base = kaggle_restaurant_repository.get_by_id(restaurant_id)
    if base is None:
        return None
    return RestaurantProfileOut(restaurant_id=base.restaurant_id, name=base.name)


def update_profile(restaurant_id: str, data: RestaurantProfileUpdate) -> Optional[RestaurantProfileOut]:
    # Returns None if the restaurant doesn't exist in the Kaggle dataset
    base = kaggle_restaurant_repository.get_by_id(restaurant_id)
    if base is None:
        return None
    return restaurant_profile_repository.upsert(restaurant_id, data, base.name)


def search_menu(food_item: str) -> list[KaggleMenuItem]:
    keyword = food_item.strip().lower()
    return [item for item in kaggle_menu_repository.list_all() if keyword in item.food_item.lower()]
