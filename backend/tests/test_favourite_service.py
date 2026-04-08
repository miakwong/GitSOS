import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import pytest
from app.schemas.favourite import FavouriteCreate, FavouriteRecord
from app.schemas.order import DeliveryMethod, Order, OrderStatus, TrafficCondition, WeatherCondition
from fastapi import HTTPException


CUSTOMER_ID = str(uuid.uuid4())
OTHER_CUSTOMER_ID = str(uuid.uuid4())
ORDER_ID = uuid.uuid4()


def make_order(order_id=None, customer_id=None, restaurant_id=16, food_item="Tacos"):
    return Order(
        order_id=order_id or ORDER_ID,
        customer_id=customer_id or CUSTOMER_ID,
        restaurant_id=restaurant_id,
        food_item=food_item,
        order_time=datetime.now(timezone.utc),
        order_value=20.0,
        delivery_distance=5.0,
        delivery_method=DeliveryMethod.BIKE,
        traffic_condition=TrafficCondition.LOW,
        weather_condition=WeatherCondition.SUNNY,
        order_status=OrderStatus.PLACED,
    )


@pytest.fixture
def temp_favourites_file(tmp_path):
    f = tmp_path / "favourites.json"
    f.write_text("[]")
    return f


@pytest.fixture(autouse=True)
def patch_data_path(temp_favourites_file):
    with patch("app.repositories.favourite_repository.DATA_PATH", str(temp_favourites_file)):
        yield


class TestAddFavourite:

    def test_add_favourite_success(self):
        from app.services import favourite_service

        order = make_order()
        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=order):
            payload = FavouriteCreate(order_id=ORDER_ID)
            result = favourite_service.add_favourite(payload, CUSTOMER_ID)

        assert result.order_id == str(ORDER_ID)
        assert result.customer_id == CUSTOMER_ID
        assert result.favourite_id is not None

    def test_add_favourite_order_not_found(self):
        from app.services import favourite_service

        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=None):
            payload = FavouriteCreate(order_id=ORDER_ID)
            with pytest.raises(HTTPException) as exc_info:
                favourite_service.add_favourite(payload, CUSTOMER_ID)
        assert exc_info.value.status_code == 404

    def test_add_favourite_duplicate_rejected(self):
        from app.services import favourite_service

        order = make_order()
        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=order):
            payload = FavouriteCreate(order_id=ORDER_ID)
            favourite_service.add_favourite(payload, CUSTOMER_ID)

            with pytest.raises(HTTPException) as exc_info:
                favourite_service.add_favourite(payload, CUSTOMER_ID)
        assert exc_info.value.status_code == 400
        assert "already in your favourites" in exc_info.value.detail


class TestGetFavourites:

    def test_get_favourites_returns_own_only(self):
        from app.services import favourite_service

        order1 = make_order()
        order2 = make_order(order_id=uuid.uuid4())

        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=order1):
            favourite_service.add_favourite(FavouriteCreate(order_id=order1.order_id), CUSTOMER_ID)

        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=order2):
            favourite_service.add_favourite(FavouriteCreate(order_id=order2.order_id), OTHER_CUSTOMER_ID)

        results = favourite_service.get_favourites(CUSTOMER_ID)
        assert len(results) == 1
        assert results[0].customer_id == CUSTOMER_ID

    def test_get_favourites_empty_list(self):
        from app.services import favourite_service

        results = favourite_service.get_favourites(CUSTOMER_ID)
        assert results == []


class TestRemoveFavourite:

    def test_remove_favourite_success(self):
        from app.services import favourite_service

        order = make_order()
        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=order):
            created = favourite_service.add_favourite(FavouriteCreate(order_id=ORDER_ID), CUSTOMER_ID)

        fav_uuid = UUID(created.favourite_id)
        favourite_service.remove_favourite(fav_uuid, CUSTOMER_ID)

        results = favourite_service.get_favourites(CUSTOMER_ID)
        assert len(results) == 0

    def test_remove_favourite_not_found(self):
        from app.services import favourite_service

        with pytest.raises(HTTPException) as exc_info:
            favourite_service.remove_favourite(uuid.uuid4(), CUSTOMER_ID)
        assert exc_info.value.status_code == 404

    def test_remove_favourite_wrong_customer(self):
        from app.services import favourite_service

        order = make_order()
        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=order):
            created = favourite_service.add_favourite(FavouriteCreate(order_id=ORDER_ID), CUSTOMER_ID)

        fav_uuid = UUID(created.favourite_id)
        with pytest.raises(HTTPException) as exc_info:
            favourite_service.remove_favourite(fav_uuid, OTHER_CUSTOMER_ID)
        assert exc_info.value.status_code == 403


class TestReorderFromFavourite:

    def test_reorder_success(self):
        from app.services import favourite_service

        order = make_order()

        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=order):
            created = favourite_service.add_favourite(FavouriteCreate(order_id=ORDER_ID), CUSTOMER_ID)

        fav_uuid = UUID(created.favourite_id)

        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=order), \
             patch.object(favourite_service._order_service, "create_order", return_value=make_order(order_id=uuid.uuid4())) as mock_create:
            new_order = favourite_service.reorder_from_favourite(fav_uuid, CUSTOMER_ID)

        assert new_order is not None
        assert new_order.order_id != ORDER_ID
        mock_create.assert_called_once()
        call_arg = mock_create.call_args[0][0]
        assert call_arg.restaurant_id == order.restaurant_id
        assert call_arg.food_item == order.food_item
        assert call_arg.delivery_method == order.delivery_method

    def test_reorder_favourite_not_found(self):
        from app.services import favourite_service

        with pytest.raises(HTTPException) as exc_info:
            favourite_service.reorder_from_favourite(uuid.uuid4(), CUSTOMER_ID)
        assert exc_info.value.status_code == 404

    def test_reorder_wrong_customer_denied(self):
        from app.services import favourite_service

        order = make_order()
        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=order):
            created = favourite_service.add_favourite(FavouriteCreate(order_id=ORDER_ID), CUSTOMER_ID)

        fav_uuid = UUID(created.favourite_id)
        with pytest.raises(HTTPException) as exc_info:
            favourite_service.reorder_from_favourite(fav_uuid, OTHER_CUSTOMER_ID)
        assert exc_info.value.status_code == 403

    def test_reorder_original_order_deleted(self):
        from app.services import favourite_service

        order = make_order()
        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=order):
            created = favourite_service.add_favourite(FavouriteCreate(order_id=ORDER_ID), CUSTOMER_ID)

        fav_uuid = UUID(created.favourite_id)

        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                favourite_service.reorder_from_favourite(fav_uuid, CUSTOMER_ID)
        assert exc_info.value.status_code == 404
        assert "no longer exists" in exc_info.value.detail

    def test_reorder_does_not_modify_original_favourite(self):
        from app.services import favourite_service

        order = make_order()
        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=order):
            created = favourite_service.add_favourite(FavouriteCreate(order_id=ORDER_ID), CUSTOMER_ID)

        fav_uuid = UUID(created.favourite_id)

        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=order), \
             patch.object(favourite_service._order_service, "create_order", return_value=make_order(order_id=uuid.uuid4())):
            favourite_service.reorder_from_favourite(fav_uuid, CUSTOMER_ID)

        favs = favourite_service.get_favourites(CUSTOMER_ID)
        assert len(favs) == 1
        assert favs[0].favourite_id == str(fav_uuid)
        assert favs[0].order_id == str(ORDER_ID)


class TestGetPopularItems:

    def test_popular_items_returns_aggregated_counts(self):
        from app.services import favourite_service

        order1 = make_order(order_id=uuid.uuid4(), food_item="Tacos")
        order2 = make_order(order_id=uuid.uuid4(), food_item="Tacos")
        order3 = make_order(order_id=uuid.uuid4(), food_item="Pizza")

        orders_map = {
            str(order1.order_id): order1,
            str(order2.order_id): order2,
            str(order3.order_id): order3,
        }

        with patch.object(favourite_service._order_repo, "get_order_by_id", side_effect=lambda oid: orders_map.get(oid)):
            favourite_service.add_favourite(FavouriteCreate(order_id=order1.order_id), CUSTOMER_ID)
            favourite_service.add_favourite(FavouriteCreate(order_id=order2.order_id), OTHER_CUSTOMER_ID)
            favourite_service.add_favourite(FavouriteCreate(order_id=order3.order_id), CUSTOMER_ID)

        with patch.object(favourite_service._order_repo, "get_order_by_id", side_effect=lambda oid: orders_map.get(oid)):
            results = favourite_service.get_popular_items()

        assert len(results) == 2
        assert results[0].food_item == "Tacos"
        assert results[0].favourite_count == 2
        assert results[1].food_item == "Pizza"
        assert results[1].favourite_count == 1

    def test_popular_items_scoped_by_restaurant(self):
        from app.services import favourite_service

        order1 = make_order(order_id=uuid.uuid4(), restaurant_id=16, food_item="Tacos")
        order2 = make_order(order_id=uuid.uuid4(), restaurant_id=99, food_item="Sushi")

        orders_map = {
            str(order1.order_id): order1,
            str(order2.order_id): order2,
        }

        with patch.object(favourite_service._order_repo, "get_order_by_id", side_effect=lambda oid: orders_map.get(oid)):
            favourite_service.add_favourite(FavouriteCreate(order_id=order1.order_id), CUSTOMER_ID)
            favourite_service.add_favourite(FavouriteCreate(order_id=order2.order_id), OTHER_CUSTOMER_ID)

        with patch.object(favourite_service._order_repo, "get_order_by_id", side_effect=lambda oid: orders_map.get(oid)):
            results = favourite_service.get_popular_items(restaurant_id=16)

        assert len(results) == 1
        assert results[0].food_item == "Tacos"
        assert results[0].restaurant_id == 16

    def test_popular_items_empty_dataset(self):
        from app.services import favourite_service

        results = favourite_service.get_popular_items()
        assert results == []

    def test_popular_items_sorted_descending(self):
        from app.services import favourite_service

        order1 = make_order(order_id=uuid.uuid4(), food_item="Burger")
        order2 = make_order(order_id=uuid.uuid4(), food_item="Tacos")
        order3 = make_order(order_id=uuid.uuid4(), food_item="Tacos")
        order4 = make_order(order_id=uuid.uuid4(), food_item="Tacos")

        orders_map = {
            str(order1.order_id): order1,
            str(order2.order_id): order2,
            str(order3.order_id): order3,
            str(order4.order_id): order4,
        }

        cust3 = str(uuid.uuid4())

        with patch.object(favourite_service._order_repo, "get_order_by_id", side_effect=lambda oid: orders_map.get(oid)):
            favourite_service.add_favourite(FavouriteCreate(order_id=order1.order_id), CUSTOMER_ID)
            favourite_service.add_favourite(FavouriteCreate(order_id=order2.order_id), CUSTOMER_ID)
            favourite_service.add_favourite(FavouriteCreate(order_id=order3.order_id), OTHER_CUSTOMER_ID)
            favourite_service.add_favourite(FavouriteCreate(order_id=order4.order_id), cust3)

        with patch.object(favourite_service._order_repo, "get_order_by_id", side_effect=lambda oid: orders_map.get(oid)):
            results = favourite_service.get_popular_items()

        assert results[0].favourite_count >= results[1].favourite_count
        assert results[0].food_item == "Tacos"
        assert results[0].favourite_count == 3

    def test_popular_items_skips_deleted_orders(self):
        from app.services import favourite_service

        order = make_order(order_id=uuid.uuid4())

        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=order):
            favourite_service.add_favourite(FavouriteCreate(order_id=order.order_id), CUSTOMER_ID)

        with patch.object(favourite_service._order_repo, "get_order_by_id", return_value=None):
            results = favourite_service.get_popular_items()

        assert results == []
