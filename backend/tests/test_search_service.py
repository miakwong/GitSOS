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


@pytest.fixture
def owner_user():
    return CurrentUser(user_id="owner1", role=Role.OWNER, owner_restaurant_ids=["R1"])


@pytest.fixture
def other_customer():
    return CurrentUser(user_id="C2", role=Role.CUSTOMER, owner_restaurant_ids=[])


# ------------------------------------------------------------------
# Filtering tests
# ------------------------------------------------------------------


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
# Scoped access tests
# ------------------------------------------------------------------


def test_admin_sees_all_orders(service, admin_user):
    # Admin should see all orders — at least the 3 from the fake repo
    # (system orders from orders.json are also merged in)
    filters = OrderFilterParams()
    pagination = PaginationParams(page=1, page_size=10)

    result = service.filter_orders(
        user=admin_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    assert result.meta.total >= 3


def test_customer_only_sees_own_orders(service, customer_user):
    # C1 has orders O1 and O3 and should not see O2, since it belongs to C2
    filters = OrderFilterParams()
    pagination = PaginationParams(page=1, page_size=10)

    result = service.filter_orders(
        user=customer_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    assert result.meta.total == 2
    assert all(order["customer_id"] == "C1" for order in result.data)


def test_customer_cannot_see_other_customers_orders(service, other_customer):
    # C2 only has O2 and should not see O1 or O3, since they belong to C1
    filters = OrderFilterParams()
    pagination = PaginationParams(page=1, page_size=10)

    result = service.filter_orders(
        user=other_customer,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    assert result.meta.total == 1
    assert result.data[0]["customer_id"] == "C2"


def test_owner_only_sees_their_restaurant_orders(service, owner_user):
    # owner1 owns R1 and should only see O1
    # O2 is at R2, O3 is at R3 — both should be excluded
    filters = OrderFilterParams()
    pagination = PaginationParams(page=1, page_size=10)

    result = service.filter_orders(
        user=owner_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    assert result.meta.total == 1
    assert result.data[0]["restaurant_id"] == "R1"
    restaurant_ids = [order["restaurant_id"] for order in result.data]
    assert "R2" not in restaurant_ids
    assert "R3" not in restaurant_ids


def test_customer_can_see_all_restaurants(service, customer_user):
    # Restaurants are public and customer should see all 3
    filters = RestaurantFilterParams()
    pagination = PaginationParams(page=1, page_size=10)

    result = service.filter_restaurants(
        user=customer_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    assert result.meta.total == 3


def test_owner_can_see_all_restaurants(service, owner_user):
    # Restaurants are public and owner should also see all 3, not just their own restaurant
    filters = RestaurantFilterParams()
    pagination = PaginationParams(page=1, page_size=10)

    result = service.filter_restaurants(
        user=owner_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    assert result.meta.total == 3


# ------------------------------------------------------------------
# Sorting tests (Feat3-B2: Pagination and Sorting)
# ------------------------------------------------------------------


def test_sort_restaurants_by_name_asc(service, admin_user):
    # "Burger Town" < "Pizza Place" < "Sushi House" alphabetically
    filters = RestaurantFilterParams()
    pagination = PaginationParams(
        page=1, page_size=10, sort_by="restaurant_name", sort_order="asc"
    )

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
    pagination = PaginationParams(
        page=1, page_size=10, sort_by="restaurant_name", sort_order="desc"
    )

    result = service.filter_restaurants(
        user=admin_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    names = [r["restaurant_name"] for r in result.data]
    assert names == ["Sushi House", "Pizza Place", "Burger Town"]


def test_sort_orders_by_value_asc(service, admin_user):
    # O2=15.00, O1=25.50, O3=30.00 — ascending should give 15, 25.5, 30
    filters = OrderFilterParams()
    pagination = PaginationParams(
        page=1, page_size=10, sort_by="order_value", sort_order="asc"
    )

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
    pagination = PaginationParams(
        page=1, page_size=10, sort_by="order_value", sort_order="desc"
    )

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
    pagination = PaginationParams(
        page=1, page_size=10, sort_by="city", sort_order="asc"
    )

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
    # Sorted order: Burger Town, Pizza Place, Sushi House
    # Page 1 of size 2 should return: Burger Town, Pizza Place
    filters = RestaurantFilterParams()
    pagination = PaginationParams(
        page=1, page_size=2, sort_by="restaurant_name", sort_order="asc"
    )

    result = service.filter_restaurants(
        user=admin_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    assert result.meta.total == 3
    assert len(result.data) == 2
    assert result.data[0]["restaurant_name"] == "Burger Town"
    assert result.data[1]["restaurant_name"] == "Pizza Place"
