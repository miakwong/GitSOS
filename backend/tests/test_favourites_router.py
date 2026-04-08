import uuid
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import UUID

import pytest
from app.dependencies import get_current_user
from app.main import app
from app.schemas.order import DeliveryMethod, Order, OrderStatus, TrafficCondition, WeatherCondition
from app.schemas.user import UserInDB
from fastapi.testclient import TestClient

client = TestClient(app)

CUSTOMER_UUID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OTHER_UUID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
ORDER_ID = uuid.uuid4()

MOCK_CUSTOMER = UserInDB(
    id=CUSTOMER_UUID,
    email="customer@test.com",
    role="customer",
    password_hash="x",
)

MOCK_OTHER_CUSTOMER = UserInDB(
    id=OTHER_UUID,
    email="other@test.com",
    role="customer",
    password_hash="x",
)

MOCK_OWNER = UserInDB(
    id=UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
    email="owner@test.com",
    role="owner",
    password_hash="x",
    restaurant_id=16,
)


def make_order(order_id=None, customer_id=None):
    return Order(
        order_id=order_id or ORDER_ID,
        customer_id=customer_id or str(CUSTOMER_UUID),
        restaurant_id=16,
        food_item="Tacos",
        order_time=datetime.now(timezone.utc),
        order_value=20.0,
        delivery_distance=5.0,
        delivery_method=DeliveryMethod.BIKE,
        traffic_condition=TrafficCondition.LOW,
        weather_condition=WeatherCondition.SUNNY,
        order_status=OrderStatus.PLACED,
    )


@pytest.fixture(autouse=True)
def patch_favourites_data(tmp_path):
    f = tmp_path / "favourites.json"
    f.write_text("[]")
    with patch("app.repositories.favourite_repository.DATA_PATH", str(f)):
        yield


@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    yield
    app.dependency_overrides.pop(get_current_user, None)


class TestAddFavouriteEndpoint:

    def test_add_favourite_success(self):
        app.dependency_overrides[get_current_user] = lambda: MOCK_CUSTOMER
        order = make_order()
        with patch("app.services.favourite_service._order_repo") as mock_repo:
            mock_repo.get_order_by_id.return_value = order
            response = client.post("/favourites/", json={"order_id": str(ORDER_ID)})

        assert response.status_code == 201
        data = response.json()
        assert data["order_id"] == str(ORDER_ID)
        assert data["customer_id"] == str(CUSTOMER_UUID)
        assert "favourite_id" in data
        assert "created_at" in data

    def test_add_favourite_order_not_found_returns_404(self):
        app.dependency_overrides[get_current_user] = lambda: MOCK_CUSTOMER
        with patch("app.services.favourite_service._order_repo") as mock_repo:
            mock_repo.get_order_by_id.return_value = None
            response = client.post("/favourites/", json={"order_id": str(uuid.uuid4())})

        assert response.status_code == 404

    def test_add_favourite_duplicate_returns_400(self):
        app.dependency_overrides[get_current_user] = lambda: MOCK_CUSTOMER
        order = make_order()
        with patch("app.services.favourite_service._order_repo") as mock_repo:
            mock_repo.get_order_by_id.return_value = order
            client.post("/favourites/", json={"order_id": str(ORDER_ID)})
            response = client.post("/favourites/", json={"order_id": str(ORDER_ID)})

        assert response.status_code == 400
        assert "already in your favourites" in response.json()["detail"]

    def test_add_favourite_non_customer_returns_403(self):
        app.dependency_overrides[get_current_user] = lambda: MOCK_OWNER
        response = client.post("/favourites/", json={"order_id": str(ORDER_ID)})
        assert response.status_code == 403

    def test_add_favourite_invalid_uuid_returns_422(self):
        app.dependency_overrides[get_current_user] = lambda: MOCK_CUSTOMER
        response = client.post("/favourites/", json={"order_id": "not-a-uuid"})
        assert response.status_code == 422


class TestListFavouritesEndpoint:

    def test_list_favourites_returns_own_entries(self):
        app.dependency_overrides[get_current_user] = lambda: MOCK_CUSTOMER
        order = make_order()
        with patch("app.services.favourite_service._order_repo") as mock_repo:
            mock_repo.get_order_by_id.return_value = order
            client.post("/favourites/", json={"order_id": str(ORDER_ID)})

        response = client.get("/favourites/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["order_id"] == str(ORDER_ID)

    def test_list_favourites_empty(self):
        app.dependency_overrides[get_current_user] = lambda: MOCK_CUSTOMER
        response = client.get("/favourites/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_favourites_non_customer_returns_403(self):
        app.dependency_overrides[get_current_user] = lambda: MOCK_OWNER
        response = client.get("/favourites/")
        assert response.status_code == 403

    def test_list_favourites_isolates_per_customer(self):
        order1 = make_order()
        order2 = make_order(order_id=uuid.uuid4(), customer_id=str(OTHER_UUID))

        app.dependency_overrides[get_current_user] = lambda: MOCK_CUSTOMER
        with patch("app.services.favourite_service._order_repo") as mock_repo:
            mock_repo.get_order_by_id.return_value = order1
            client.post("/favourites/", json={"order_id": str(order1.order_id)})

        app.dependency_overrides[get_current_user] = lambda: MOCK_OTHER_CUSTOMER
        with patch("app.services.favourite_service._order_repo") as mock_repo:
            mock_repo.get_order_by_id.return_value = order2
            client.post("/favourites/", json={"order_id": str(order2.order_id)})

        app.dependency_overrides[get_current_user] = lambda: MOCK_CUSTOMER
        response = client.get("/favourites/")
        data = response.json()
        assert len(data) == 1
        assert data[0]["customer_id"] == str(CUSTOMER_UUID)


class TestRemoveFavouriteEndpoint:

    def test_remove_favourite_success(self):
        app.dependency_overrides[get_current_user] = lambda: MOCK_CUSTOMER
        order = make_order()
        with patch("app.services.favourite_service._order_repo") as mock_repo:
            mock_repo.get_order_by_id.return_value = order
            create_response = client.post("/favourites/", json={"order_id": str(ORDER_ID)})

        fav_id = create_response.json()["favourite_id"]
        delete_response = client.delete(f"/favourites/{fav_id}")
        assert delete_response.status_code == 204

        list_response = client.get("/favourites/")
        assert list_response.json() == []

    def test_remove_favourite_not_found_returns_404(self):
        app.dependency_overrides[get_current_user] = lambda: MOCK_CUSTOMER
        response = client.delete(f"/favourites/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_remove_favourite_wrong_customer_returns_403(self):
        app.dependency_overrides[get_current_user] = lambda: MOCK_CUSTOMER
        order = make_order()
        with patch("app.services.favourite_service._order_repo") as mock_repo:
            mock_repo.get_order_by_id.return_value = order
            create_response = client.post("/favourites/", json={"order_id": str(ORDER_ID)})

        fav_id = create_response.json()["favourite_id"]

        app.dependency_overrides[get_current_user] = lambda: MOCK_OTHER_CUSTOMER
        response = client.delete(f"/favourites/{fav_id}")
        assert response.status_code == 403

    def test_remove_favourite_non_customer_returns_403(self):
        app.dependency_overrides[get_current_user] = lambda: MOCK_OWNER
        response = client.delete(f"/favourites/{uuid.uuid4()}")
        assert response.status_code == 403
