import pytest
from app.repositories.search_repo import SearchRepository
from app.schemas.search_filters import (
    CurrentUser,
    OrderFilterParams,
    PaginationParams,
    RestaurantFilterParams,
    Role,
)
from app.services.search_service import SearchService
from fastapi import HTTPException


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


def test_unsupported_filter_raises_422(service, admin_user):
    filters = RestaurantFilterParams()
    pagination = PaginationParams(page=1, page_size=10)

    with pytest.raises(HTTPException) as exc_info:
        service.filter_restaurants(
            user=admin_user,
            filters=filters,
            pagination=pagination,
            raw_query_params={"bad_filter": "test"},
        )

    assert exc_info.value.status_code == 422
    assert "Unsupported query parameter" in exc_info.value.detail["message"]


# ------------------------------------------------------------------
# Feat3-B2: Sorting tests
# ------------------------------------------------------------------

def test_sort_restaurants_by_name_asc(service, admin_user):
    # "Burger Town" < "Pizza Place" < "Sushi House" alphabetically
    filters = RestaurantFilterParams()
    pagination = PaginationParams(page=1, page_size=10, sort_by="restaurant_name", sort_order="asc")

    result = service.filter_restaurants(
        user=admin_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    names = [r["restaurant_name"] for r in result.data]
    assert names == ["Burger Town", "Pizza Place", "Sushi House"]


def test_sort_restaurants_by_name_desc(service, admin_user):
    filters = RestaurantFilterParams()
    pagination = PaginationParams(page=1, page_size=10, sort_by="restaurant_name", sort_order="desc")

    result = service.filter_restaurants(
        user=admin_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    names = [r["restaurant_name"] for r in result.data]
    assert names == ["Sushi House", "Pizza Place", "Burger Town"]


def test_sort_orders_by_value_asc(service, admin_user):
    # O2=15.00, O1=25.50, O3=30.00
    filters = OrderFilterParams()
    pagination = PaginationParams(page=1, page_size=10, sort_by="order_value", sort_order="asc")

    result = service.filter_orders(
        user=admin_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    values = [r["order_value"] for r in result.data]
    assert values == sorted(values)


def test_sort_orders_by_value_desc(service, admin_user):
    filters = OrderFilterParams()
    pagination = PaginationParams(page=1, page_size=10, sort_by="order_value", sort_order="desc")

    result = service.filter_orders(
        user=admin_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    values = [r["order_value"] for r in result.data]
    assert values == sorted(values, reverse=True)


def test_invalid_sort_by_raises_400(service, admin_user):
    # "city" is not a valid sort key for restaurants
    filters = RestaurantFilterParams()
    pagination = PaginationParams(page=1, page_size=10, sort_by="city", sort_order="asc")

    with pytest.raises(HTTPException) as exc_info:
        service.filter_restaurants(
            user=admin_user,
            filters=filters,
            pagination=pagination,
            raw_query_params={},
        )

    assert exc_info.value.status_code == 400


def test_sort_and_pagination_work_together(service, admin_user):
    # Sort asc by name, then take only page 1 with page_size=2
    # Burger Town, Pizza Place, Sushi House — page 1 of 2 = Burger Town, Pizza Place
    filters = RestaurantFilterParams()
    pagination = PaginationParams(page=1, page_size=2, sort_by="restaurant_name", sort_order="asc")

    result = service.filter_restaurants(
        user=admin_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    assert result.meta.total == 3         # all 3 restaurants exist
    assert len(result.data) == 2          # only 2 returned due to page_size
    assert result.data[0]["restaurant_name"] == "Burger Town"
    assert result.data[1]["restaurant_name"] == "Pizza Place"
