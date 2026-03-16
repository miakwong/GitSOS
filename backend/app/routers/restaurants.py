from app.dependencies import get_current_owner
from app.schemas.kaggle import KaggleMenuItem, KaggleRestaurant
from app.schemas.menu import MenuItemCreate, MenuItemOut, MenuItemUpdate
from app.services import menu_service, restaurant_service
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("", response_model=list[KaggleRestaurant])
def list_restaurants():
    return restaurant_service.list_restaurants()


@router.get("/{restaurant_id}", response_model=KaggleRestaurant)
def get_restaurant(restaurant_id: str):
    result = restaurant_service.get_restaurant(restaurant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return result


@router.get("/{restaurant_id}/menu", response_model=list[KaggleMenuItem])
def get_menu(restaurant_id: str):
    result = restaurant_service.get_menu_for_restaurant(restaurant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return result


@router.get("/{restaurant_id}/menu/items", response_model=list[MenuItemOut])
def list_owner_menu_items(restaurant_id: str):
    return menu_service.get_menu_items(restaurant_id)


@router.post("/{restaurant_id}/menu/items", response_model=MenuItemOut, status_code=201)
def add_menu_item(
    restaurant_id: str,
    body: MenuItemCreate,
    owner: tuple = Depends(get_current_owner),
):
    if str(owner[1]) != restaurant_id:
        raise HTTPException(status_code=403, detail="Not authorized for this restaurant")
    return menu_service.create_menu_item(restaurant_id, body)


@router.put("/{restaurant_id}/menu/items/{food_item}", response_model=MenuItemOut)
def update_menu_item(
    restaurant_id: str,
    food_item: str,
    body: MenuItemUpdate,
    owner: tuple = Depends(get_current_owner),
):
    if str(owner[1]) != restaurant_id:
        raise HTTPException(status_code=403, detail="Not authorized for this restaurant")
    result = menu_service.update_menu_item(restaurant_id, food_item, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return result


@router.delete("/{restaurant_id}/menu/items/{food_item}", status_code=204)
def delete_menu_item(
    restaurant_id: str,
    food_item: str,
    owner: tuple = Depends(get_current_owner),
):
    if str(owner[1]) != restaurant_id:
        raise HTTPException(status_code=403, detail="Not authorized for this restaurant")
    found = menu_service.delete_menu_item(restaurant_id, food_item)
    if not found:
        raise HTTPException(status_code=404, detail="Menu item not found")
