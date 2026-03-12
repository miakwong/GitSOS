from typing import Optional

from app.repositories import kaggle_menu_repository, kaggle_restaurant_repository
from app.schemas.kaggle import KaggleMenuItem, KaggleRestaurant


def list_restaurants() -> list[KaggleRestaurant]:
    """Return all unique restaurants derived from the Kaggle dataset."""
    return kaggle_restaurant_repository.list_all()


def get_restaurant(restaurant_id: str) -> Optional[KaggleRestaurant]:
    """Return a single restaurant by ID, or None if not found."""
    return kaggle_restaurant_repository.get_by_id(restaurant_id)


def get_menu(restaurant_id: str) -> list[KaggleMenuItem]:
    """Return all menu items for a restaurant with precomputed median prices."""
    return kaggle_menu_repository.get_by_restaurant(restaurant_id)


def get_median_price(food_item: str) -> Optional[float]:
    """
    Return the median order_value for a food item across the entire dataset.
    Used by pricing_service to compute order subtotal.

    Example:
        price = get_median_price("Pasta")  # → 35.0
        if price is None:
            raise ValueError("Unknown food item")
    """
    return kaggle_menu_repository.get_median_price(food_item)
