from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, Request

from schemas.search_filters import (
    CurrentUser,
    PaginationParams,
    RestaurantFilterParams,
    MenuItemFilterParams,
    OrderFilterParams,
    PaginatedResponse,
)
from services.search_service import SearchService

# If there is already a final auth in dependencies.py, it could be imported here.
# Example:
# from dependencies import get_current_user

def get_current_user_mock() -> CurrentUser:
    """
    Replace with the real dependency:
        return get_current_user()
    """
    return CurrentUser(user_id="demo-user", role="admin", owner_restaurant_ids=[])


router = APIRouter(prefix="/search", tags=["Search & Filters"])
service = SearchService()


@router.get("/restaurants", response_model=PaginatedResponse)
def search_restaurants(
    request: Request,
    restaurant_id: Optional[str] = None,
    restaurant_name: Optional[str] = None,
    city: Optional[str] = None,
    cuisine: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user_mock),
):
    filters = RestaurantFilterParams(
        restaurant_id=restaurant_id,
        restaurant_name=restaurant_name,
        city=city,
        cuisine=cuisine,
    )
    pagination = PaginationParams(page=page, page_size=page_size)

    raw_query_params: Dict[str, Any] = dict(request.query_params)
    return service.filter_restaurants(user, filters, pagination, raw_query_params)


@router.get("/menu-items", response_model=PaginatedResponse)
def search_menu_items(
    request: Request,
    restaurant_id: Optional[str] = None,
    item_name: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user_mock),
):
    filters = MenuItemFilterParams(
        restaurant_id=restaurant_id,
        item_name=item_name,
        category=category,
        min_price=min_price,
        max_price=max_price,
    )
    pagination = PaginationParams(page=page, page_size=page_size)

    raw_query_params: Dict[str, Any] = dict(request.query_params)
    return service.filter_menu_items(user, filters, pagination, raw_query_params)


@router.get("/orders", response_model=PaginatedResponse)
def search_orders(
    request: Request,
    order_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    restaurant_id: Optional[str] = None,
    order_status: Optional[str] = None,
    min_order_value: Optional[float] = Query(None, ge=0),
    max_order_value: Optional[float] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user_mock),
):
    filters = OrderFilterParams(
        order_id=order_id,
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        order_status=order_status,
        min_order_value=min_order_value,
        max_order_value=max_order_value,
    )
    pagination = PaginationParams(page=page, page_size=page_size)

    raw_query_params: Dict[str, Any] = dict(request.query_params)
    return service.filter_orders(user, filters, pagination, raw_query_params)