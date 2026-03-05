from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, conint


class Role(str, Enum):
    CUSTOMER = "customer"
    OWNER = "owner"
    ADMIN = "admin"


class CurrentUser(BaseModel):
    """
    If the user schema is implemented, then the below could be replace and keep the same fields.
    """
    user_id: str
    role: Role
    owner_restaurant_ids: List[str] = []


class PaginationParams(BaseModel):
    page: conint(ge=1) = 1
    page_size: conint(ge=1, le=100) = 20  # This line is to protect server from large data requests.
    sort_by: Optional[str] = None
    sort_order: Literal["asc", "desc"] = "asc"


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int


class PaginatedResponse(BaseModel):
    meta: PageMeta
    data: List[Dict[str, Any]]


# ---------------------------
# Filter schemas (whitelists)
# ---------------------------

class RestaurantFilterParams(BaseModel):
    """
    Only include filters the server supports.
    """
    restaurant_id: Optional[str] = None
    restaurant_name: Optional[str] = None
    city: Optional[str] = None
    cuisine: Optional[str] = None


class MenuItemFilterParams(BaseModel):
    restaurant_id: Optional[str] = None
    item_name: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = Field(default=None, ge=0)
    max_price: Optional[float] = Field(default=None, ge=0)


class OrderFilterParams(BaseModel):
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    restaurant_id: Optional[str] = None
    order_status: Optional[str] = None
    min_order_value: Optional[float] = Field(default=None, ge=0)
    max_order_value: Optional[float] = Field(default=None, ge=0)