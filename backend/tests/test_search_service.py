import pytest
from fastapi import HTTPException

from app.repositories.search_repo import SearchRepository
from app.schemas.search_filters import (
    CurrentUser,
    Role,
    PaginationParams,
    RestaurantFilterParams,
    OrderFilterParams,
)
from app.services.search_service import SearchService


class FakeSearchRepository(SearchRepository):
    def load_all_rows(self):
        return [
            {
                "restaurant_id": "R1",
                "restaurant_name": "Sushi House",
                "city": "Kelowna",
                "cuisine": "Japanese",
                "customer_id": "C1",
                "order_id": "O1",
                "order_status": "Delivered",
                "order_value": "25.50",
            },
            {
                "restaurant_id": "R2",
                "restaurant_name": "Burger Town",
                "city": "Vancouver",
                "cuisine": "Fast Food",
                "customer_id": "C2",
                "order_id": "O2",
                "order_status": "Placed",
                "order_value": "15.00",
            },
            {
                "restaurant_id": "R3",
                "restaurant_name": "Pizza Place",
                "city": "Kelowna",
                "cuisine": "Italian",
                "customer_id": "C1",
                "order_id": "O3",
                "order_status": "Paid",
                "order_value": "30.00",
            },
        ]


@pytest.fixture
def service():
    return SearchService(repo=FakeSearchRepository())


@pytest.fixture
def admin_user():
    return CurrentUser(user_id="admin1", role=Role.ADMIN, owner_restaurant_ids=[])


@pytest.fixture
def customer_user():
    return CurrentUser(user_id="C1", role=Role.CUSTOMER, owner_restaurant_ids=[])


def test_filter_restaurants_by_city(service, admin_user):
    filters = RestaurantFilterParams(city="Kelowna")
    pagination = PaginationParams(page=1, page_size=10)

    result = service.filter_restaurants(
        user=admin_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={"city": "Kelowna"},
    )

    assert result.meta.total == 2
    assert len(result.data) == 2
    assert all(item["city"] == "Kelowna" for item in result.data)


def test_filter_orders_customer_scope(service, customer_user):
    filters = OrderFilterParams()
    pagination = PaginationParams(page=1, page_size=10)

    result = service.filter_orders(
        user=customer_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    assert result.meta.total == 2
    assert len(result.data) == 2
    assert all(order["customer_id"] == "C1" for order in result.data)


def test_unsupported_filter_raises_400(service, admin_user):
    filters = RestaurantFilterParams()
    pagination = PaginationParams(page=1, page_size=10)

    with pytest.raises(HTTPException) as exc_info:
        service.filter_restaurants(
            user=admin_user,
            filters=filters,
            pagination=pagination,
            raw_query_params={"bad_filter": "test"},
        )

    assert exc_info.value.status_code == 400
    assert "Unsupported filter" in exc_info.value.detail["message"]