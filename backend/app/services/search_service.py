from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.repositories.search_repo import SearchRepository
from app.schemas.search_filters import (
    CurrentUser,
    MenuItemFilterParams,
    OrderFilterParams,
    PageMeta,
    PaginatedResponse,
    PaginationParams,
    RestaurantFilterParams,
)
from app.services.query_validation_service import QueryValidationService
from app.services.sort_helper import (
    VALID_MENU_ITEM_SORT_KEYS,
    VALID_ORDER_SORT_KEYS,
    VALID_RESTAURANT_SORT_KEYS,
    sort_results,
)
from fastapi import HTTPException

_DEFAULT_SYSTEM_ORDERS_FILE = (
    Path(__file__).resolve().parent.parent / "data" / "orders.json"
)


# -------------------------
# Helper: safe parsing
# -------------------------
def _to_float(val: Any) -> Optional[float]:
    try:
        if val is None or val == "":
            return None
        return float(val)
    except Exception:
        return None


def _contains(hay: Any, needle: str) -> bool:
    if hay is None:
        return False
    return needle.lower() in str(hay).lower()


# -------------------------
# Whitelist
# -------------------------
ALLOWED_RESTAURANT_FILTERS = {"restaurant_id", "restaurant_name", "city", "cuisine"}
ALLOWED_MENU_FILTERS = {
    "restaurant_id",
    "item_name",
    "category",
    "min_price",
    "max_price",
}
ALLOWED_ORDER_FILTERS = {
    "order_id",
    "customer_id",
    "restaurant_id",
    "order_status",
    "min_order_value",
    "max_order_value",
}


class SearchService:
    def __init__(self, repo: Optional[SearchRepository] = None) -> None:
        self.repo = repo or SearchRepository()

    def _enforce_scope(
        self, user: CurrentUser, row: Dict[str, Any], resource: str
    ) -> bool:
        # Admin sees everything with no restrictions
        if user.role.value == "admin":
            return True

        # Restaurants and menu items are public so all roles can browse them
        if resource in ("restaurants", "menu_items"):
            return True

        # Orders are private so it needs to be restricted based on the user's role
        if resource == "orders":
            if user.role.value == "customer":
                # Customer can only see their own orders
                row_customer = str(row.get("customer_id") or "")
                return row_customer == user.user_id

            if user.role.value == "owner":
                # Owner can only see orders placed at their own restaurants.
                # If owner_restaurant_ids is empty, no orders will match — this is intentional.
                # An owner with no assigned restaurants should see nothing, not everything.
                row_restaurant = str(row.get("restaurant_id") or "")
                return row_restaurant in user.owner_restaurant_ids

        # Deny by default which is unknown resource or role
        return False

    def _reject_unsupported_filters(
        self, provided: Dict[str, Any], allowed: set[str]
    ) -> None:
        unsupported = [
            k for k, v in provided.items() if v not in (None, "") and k not in allowed
        ]
        if unsupported:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Unsupported filter parameter(s).",
                    "unsupported": unsupported,
                    "allowed": sorted(list(allowed)),
                },
            )

    def _paginate(
        self, rows: List[Dict[str, Any]], p: PaginationParams
    ) -> Tuple[List[Dict[str, Any]], int]:
        total = len(rows)
        start = (p.page - 1) * p.page_size
        end = start + p.page_size
        return rows[start:end], total

    # -------------------------
    # Restaurants search/filter
    # -------------------------
    def filter_restaurants(
        self,
        user: CurrentUser,
        filters: RestaurantFilterParams,
        pagination: PaginationParams,
        raw_query_params: Dict[str, Any],
    ) -> PaginatedResponse:
        QueryValidationService.reject_unsupported_filters(
            raw_query_params,
            ALLOWED_RESTAURANT_FILTERS,
        )

        rows = self.repo.load_all_rows()

        # Below is to build a "restaurant view" from rows:
        # The dataset may have repeated restaurant info across many rows, so we de-duplicate by restaurant_id/name.
        seen = set()
        restaurants: List[Dict[str, Any]] = []
        for r in rows:
            rid = str(r.get("restaurant_id") or r.get("RestaurantID") or "")
            rname = str(
                r.get("restaurant_name")
                or r.get("Restaurant")
                or r.get("restaurant")
                or ""
            )
            key = (rid, rname)
            if key in seen:
                continue
            seen.add(key)

            # Construct minimal restaurant record
            restaurants.append(
                {
                    "restaurant_id": rid,
                    "restaurant_name": rname,
                    "city": r.get("city") or r.get("City") or r.get("location"),
                    "cuisine": r.get("cuisine")
                    or r.get("Cuisine")
                    or r.get("preferred_cuisine"),
                }
            )

        # Apply filters (case-insensitive contains for names/city/cuisine)
        out = restaurants

        if filters.restaurant_id:
            out = [
                x for x in out if str(x.get("restaurant_id")) == filters.restaurant_id
            ]

        if filters.restaurant_name:
            out = [
                x
                for x in out
                if _contains(x.get("restaurant_name"), filters.restaurant_name)
            ]

        if filters.city:
            out = [x for x in out if _contains(x.get("city"), filters.city)]

        if filters.cuisine:
            out = [x for x in out if _contains(x.get("cuisine"), filters.cuisine)]

        # Scope (usually public for restaurants, but keep hook)
        out = [x for x in out if self._enforce_scope(user, x, "restaurants")]

        # Sort before paginating
        out = sort_results(
            out, pagination.sort_by, pagination.sort_order, VALID_RESTAURANT_SORT_KEYS
        )

        page_rows, total = self._paginate(out, pagination)
        return PaginatedResponse(
            meta=PageMeta(
                page=pagination.page, page_size=pagination.page_size, total=total
            ),
            data=page_rows,
        )

    # -------------------------
    # Menu items search/filter
    # -------------------------
    def filter_menu_items(
        self,
        user: CurrentUser,
        filters: MenuItemFilterParams,
        pagination: PaginationParams,
        raw_query_params: Dict[str, Any],
    ) -> PaginatedResponse:
        QueryValidationService.reject_unsupported_filters(
            raw_query_params,
            ALLOWED_MENU_FILTERS,
        )

        QueryValidationService.validate_price_range(
            filters.min_price,
            filters.max_price,
        )

        rows = self.repo.load_all_rows()

        # Create "menu item view" from csv rows (depends on your column names; adjust as needed)
        items: List[Dict[str, Any]] = []
        for r in rows:
            items.append(
                {
                    "restaurant_id": str(
                        r.get("restaurant_id") or r.get("RestaurantID") or ""
                    ),
                    "item_name": r.get("item_name")
                    or r.get("FoodItem")
                    or r.get("food_item"),
                    "category": r.get("category")
                    or r.get("Category")
                    or r.get("preferred_cuisine"),
                    "price": _to_float(
                        r.get("price")
                        or r.get("Price")
                        or r.get("item_price")
                        or r.get("order_value")
                    ),
                }
            )

        out = items

        if filters.restaurant_id:
            out = [x for x in out if x.get("restaurant_id") == filters.restaurant_id]

        if filters.item_name:
            out = [x for x in out if _contains(x.get("item_name"), filters.item_name)]

        if filters.category:
            out = [x for x in out if _contains(x.get("category"), filters.category)]

        if filters.min_price is not None:
            out = [
                x
                for x in out
                if (x.get("price") is not None and x["price"] >= filters.min_price)
            ]

        if filters.max_price is not None:
            out = [
                x
                for x in out
                if (x.get("price") is not None and x["price"] <= filters.max_price)
            ]

        out = [x for x in out if self._enforce_scope(user, x, "menu_items")]

        # Sort before paginating
        out = sort_results(
            out, pagination.sort_by, pagination.sort_order, VALID_MENU_ITEM_SORT_KEYS
        )

        page_rows, total = self._paginate(out, pagination)
        return PaginatedResponse(
            meta=PageMeta(
                page=pagination.page, page_size=pagination.page_size, total=total
            ),
            data=page_rows,
        )

    # -------------------------
    # Orders search/filter
    # -------------------------
    def filter_orders(
        self,
        user: CurrentUser,
        filters: OrderFilterParams,
        pagination: PaginationParams,
        raw_query_params: Dict[str, Any],
    ) -> PaginatedResponse:
        QueryValidationService.reject_unsupported_filters(
            raw_query_params,
            ALLOWED_ORDER_FILTERS,
        )

        QueryValidationService.validate_order_value_range(
            filters.min_order_value,
            filters.max_order_value,
        )

        rows = self.repo.load_all_rows()

        # Create a simplified "order view" from rows (adjust column names to match your CSV)
        orders: List[Dict[str, Any]] = []
        for r in rows:
            orders.append(
                {
                    "order_id": str(
                        r.get("order_id") or r.get("OrderID") or r.get("id") or ""
                    ),
                    "customer_id": str(
                        r.get("customer_id")
                        or r.get("CustomerID")
                        or r.get("customer")
                        or ""
                    ),
                    "restaurant_id": str(
                        r.get("restaurant_id") or r.get("RestaurantID") or ""
                    ),
                    "order_status": r.get("order_status")
                    or r.get("OrderStatus")
                    or r.get("food_condition"),
                    "order_value": _to_float(
                        r.get("order_value") or r.get("OrderValue")
                    ),
                }
            )

        # Also include system orders from orders.json
        if _DEFAULT_SYSTEM_ORDERS_FILE.exists():
            system_orders = json.loads(
                _DEFAULT_SYSTEM_ORDERS_FILE.read_text(encoding="utf-8")
            )
            for r in system_orders:
                orders.append(
                    {
                        "order_id": str(r.get("order_id") or ""),
                        "customer_id": str(r.get("customer_id") or ""),
                        "restaurant_id": str(r.get("restaurant_id") or ""),
                        "order_status": r.get("order_status") or "",
                        "order_value": _to_float(r.get("order_value")),
                        "food_item": r.get("food_item") or "",
                        "order_time": r.get("order_time") or "",
                    }
                )

        out = orders

        if filters.order_id:
            out = [x for x in out if x.get("order_id") == filters.order_id]

        if filters.customer_id:
            out = [x for x in out if x.get("customer_id") == filters.customer_id]

        if filters.restaurant_id:
            out = [x for x in out if x.get("restaurant_id") == filters.restaurant_id]

        if filters.order_status:
            out = [
                x for x in out if _contains(x.get("order_status"), filters.order_status)
            ]

        if filters.min_order_value is not None:
            out = [
                x
                for x in out
                if (
                    x.get("order_value") is not None
                    and x["order_value"] >= filters.min_order_value
                )
            ]

        if filters.max_order_value is not None:
            out = [
                x
                for x in out
                if (
                    x.get("order_value") is not None
                    and x["order_value"] <= filters.max_order_value
                )
            ]

        # Enforce authorized scope for orders
        out = [x for x in out if self._enforce_scope(user, x, "orders")]

        # Sort before paginating
        out = sort_results(
            out, pagination.sort_by, pagination.sort_order, VALID_ORDER_SORT_KEYS
        )

        page_rows, total = self._paginate(out, pagination)
        return PaginatedResponse(
            meta=PageMeta(
                page=pagination.page, page_size=pagination.page_size, total=total
            ),
            data=page_rows,
        )
