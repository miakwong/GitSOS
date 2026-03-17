from unittest.mock import patch
from uuid import uuid4

import pytest
from app.dependencies import get_current_owner
from app.main import app
from app.schemas.restaurant_profile import RestaurantProfileOut
from fastapi.testclient import TestClient

client = TestClient(app)

OWNER_ID = uuid4()
RESTAURANT_ID = "10"
OWNER_RESTAURANT_INT = 10

PROFILE = RestaurantProfileOut(restaurant_id=RESTAURANT_ID, name="Pizza Place")


@pytest.fixture(autouse=True)
def mock_owner():
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, OWNER_RESTAURANT_INT)
    yield
    app.dependency_overrides.pop(get_current_owner, None)


@pytest.fixture(autouse=True)
def mock_svc():
    with patch("app.routers.restaurants.restaurant_service") as mock:
        mock.get_profile.return_value = PROFILE
        mock.update_profile.return_value = PROFILE
        yield mock


# GET /restaurants/{id}/profile

def test_get_profile_200(mock_svc):
    response = client.get(f"/restaurants/{RESTAURANT_ID}/profile")
    assert response.status_code == 200


def test_get_profile_returns_data(mock_svc):
    data = client.get(f"/restaurants/{RESTAURANT_ID}/profile").json()
    assert data["restaurant_id"] == RESTAURANT_ID
    assert data["name"] == "Pizza Place"


def test_get_profile_not_found(mock_svc):
    mock_svc.get_profile.return_value = None
    response = client.get("/restaurants/999/profile")
    assert response.status_code == 404
    assert response.json()["detail"] == "Restaurant not found"


def test_get_profile_no_auth_required(mock_svc):
    # GET profile is public (no token needed)
    app.dependency_overrides.pop(get_current_owner, None)
    response = client.get(f"/restaurants/{RESTAURANT_ID}/profile")
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, OWNER_RESTAURANT_INT)
    assert response.status_code == 200


# PUT /restaurants/{id}/profile

def test_update_profile_200(mock_svc):
    response = client.put(
        f"/restaurants/{RESTAURANT_ID}/profile",
        json={"name": "Pizza Place"},
    )
    assert response.status_code == 200


def test_update_profile_returns_updated_data(mock_svc):
    data = client.put(
        f"/restaurants/{RESTAURANT_ID}/profile",
        json={"name": "Pizza Place"},
    ).json()
    assert data["name"] == "Pizza Place"
    assert data["restaurant_id"] == RESTAURANT_ID


def test_update_profile_empty_body_200(mock_svc):
    # empty body is valid (no fields required)
    response = client.put(
        f"/restaurants/{RESTAURANT_ID}/profile",
        json={},
    )
    assert response.status_code == 200


def test_update_profile_empty_name_422(mock_svc):
    response = client.put(
        f"/restaurants/{RESTAURANT_ID}/profile",
        json={"name": ""},
    )
    assert response.status_code == 422


def test_update_profile_whitespace_name_422(mock_svc):
    response = client.put(
        f"/restaurants/{RESTAURANT_ID}/profile",
        json={"name": "   "},
    )
    assert response.status_code == 422


def test_update_profile_not_found_404(mock_svc):
    mock_svc.update_profile.return_value = None
    response = client.put(
        f"/restaurants/{RESTAURANT_ID}/profile",
        json={"name": "Pizza Place"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Restaurant not found"


def test_update_profile_wrong_restaurant_403(mock_svc):
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, 99)
    response = client.put(
        f"/restaurants/{RESTAURANT_ID}/profile",
        json={"name": "Pizza Place"},
    )
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, OWNER_RESTAURANT_INT)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized for this restaurant"


def test_update_profile_no_auth_401(mock_svc):
    app.dependency_overrides.pop(get_current_owner, None)
    response = client.put(
        f"/restaurants/{RESTAURANT_ID}/profile",
        json={"name": "Pizza Place"},
    )
    app.dependency_overrides[get_current_owner] = lambda: (OWNER_ID, OWNER_RESTAURANT_INT)
    assert response.status_code == 401
