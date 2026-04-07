from __future__ import annotations

from typing import Any, Dict, Optional

from app.dependencies import get_current_user_full
from app.schemas.search_filters import (
    CurrentUser,
    MenuItemFilterParams,
    OrderFilterParams,
    PaginatedResponse,
    PaginationParams,
    RestaurantFilterParams,
)
from app.schemas.user import UserInDB
from app.services.search_service import SearchService
from fastapi import APIRouter, Depends, Query, Request
from fastapi.security import OAuth2PasswordBearer

oauth2_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

_GUEST_USER = CurrentUser(user_id="guest", role="admin", owner_restaurant_ids=[])


def _to_current_user(user: UserInDB) -> CurrentUser:
    restaurant_ids = [str(user.restaurant_id)] if user.restaurant_id is not None else []
    return CurrentUser(
        user_id=str(user.id), role=user.role, owner_restaurant_ids=restaurant_ids
    )


def get_search_user(user: UserInDB = Depends(get_current_user_full)) -> CurrentUser:
    return _to_current_user(user)


async def get_optional_search_user(
    token: Optional[str] = Depends(oauth2_optional),
) -> CurrentUser:
    """Public endpoints: returns guest user when unauthenticated."""
    if not token:
        return _GUEST_USER
    import jwt
    from app.dependencies import ALGORITHM, SECRET_KEY, get_user_repo
    from app.services.auth_service import TOKEN_BLACKLIST

    try:
        if token in TOKEN_BLACKLIST:
            return _GUEST_USER
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_repo = get_user_repo()
        from uuid import UUID

        user = user_repo.get_user_by_id(UUID(payload["sub"]))
        if user is None:
            return _GUEST_USER
        return _to_current_user(user)
    except Exception:
        return _GUEST_USER


router = APIRouter(prefix="/search", tags=["Search & Filters"])
service = SearchService()


PAGINATION_AND_SORT_PARAMS = {"page", "page_size", "sort_by", "sort_order"}


def _filter_only_params(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in raw.items() if k not in PAGINATION_AND_SORT_PARAMS}


@router.get("/restaurants", response_model=PaginatedResponse)
def search_restaurants(
    request: Request,
    restaurant_id: Optional[str] = None,
    restaurant_name: Optional[str] = None,
    city: Optional[str] = None,
    cuisine: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(
        None, description="Sort by: restaurant_id, restaurant_name"
    ),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="asc or desc"),
    user: CurrentUser = Depends(get_optional_search_user),
):
    filters = RestaurantFilterParams(
        restaurant_id=restaurant_id,
        restaurant_name=restaurant_name,
        city=city,
        cuisine=cuisine,
    )
    pagination = PaginationParams(
        page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
    )

    raw_query_params = _filter_only_params(dict(request.query_params))
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
    sort_by: Optional[str] = Query(None, description="Sort by: item_name, price"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="asc or desc"),
    user: CurrentUser = Depends(get_optional_search_user),
):
    filters = MenuItemFilterParams(
        restaurant_id=restaurant_id,
        item_name=item_name,
        category=category,
        min_price=min_price,
        max_price=max_price,
    )
    pagination = PaginationParams(
        page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
    )

    raw_query_params = _filter_only_params(dict(request.query_params))
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
    sort_by: Optional[str] = Query(None, description="Sort by: order_id, order_value"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="asc or desc"),
    user: CurrentUser = Depends(get_search_user),
):
    filters = OrderFilterParams(
        order_id=order_id,
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        order_status=order_status,
        min_order_value=min_order_value,
        max_order_value=max_order_value,
    )
    pagination = PaginationParams(
        page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
    )

    raw_query_params = _filter_only_params(dict(request.query_params))
    return service.filter_orders(user, filters, pagination, raw_query_params)
