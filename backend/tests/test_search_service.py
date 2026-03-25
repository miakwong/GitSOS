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


def test_admin_sees_all_orders(service, admin_user):
    # Admin should see all the 3 orders with no restrictions
    filters = OrderFilterParams()
    pagination = PaginationParams(page=1, page_size=10)

    result = service.filter_orders(
        user=admin_user,
        filters=filters,
        pagination=pagination,
        raw_query_params={},
    )

    assert result.meta.total == 3


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
    # C2 only has O2 and should not see O1 or O3, since it belong to C1
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
