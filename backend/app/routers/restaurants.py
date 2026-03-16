
from app.schemas.kaggle import KaggleMenuItem, KaggleRestaurant
from app.services import restaurant_service
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("", response_model=list[KaggleRestaurant])
def list_restaurants():
    """Return all restaurants derived from the Kaggle dataset."""
    return restaurant_service.list_restaurants()


@router.get("/{restaurant_id}", response_model=KaggleRestaurant)
def get_restaurant(restaurant_id: str):
    """Return a single restaurant by ID."""
    result = restaurant_service.get_restaurant(restaurant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return result


@router.get("/{restaurant_id}/menu", response_model=list[KaggleMenuItem])
def get_menu(restaurant_id: str):
    """Return all menu items for a restaurant. Returns 404 if restaurant not found."""
    result = restaurant_service.get_menu_for_restaurant(restaurant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return result
