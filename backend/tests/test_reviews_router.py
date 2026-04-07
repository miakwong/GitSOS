import uuid
from unittest.mock import patch

import pytest
from app.dependencies import get_current_user
from app.main import app
from app.schemas.review import ReviewOut
from app.schemas.user import UserInDB
from fastapi.testclient import TestClient

ORDER_ID = uuid.uuid4()
REVIEW_ID = uuid.uuid4()
CUSTOMER_ID = uuid.uuid4()
RESTAURANT_ID = 5

MOCK_CUSTOMER = UserInDB(
    id=CUSTOMER_ID,
    email="customer@test.com",
    role="customer",
    password_hash="hashed",
)

MOCK_OWNER = UserInDB(
    id=uuid.uuid4(),
    email="owner@test.com",
    role="owner",
    password_hash="hashed",
    restaurant_id=RESTAURANT_ID,
)

MOCK_REVIEW_OUT = ReviewOut(
    review_id=str(REVIEW_ID),
    order_id=str(ORDER_ID),
    customer_id=str(CUSTOMER_ID),
    restaurant_id=RESTAURANT_ID,
    rating=4,
    tags=["Delicious", "Fast delivery"],
    created_at="2025-01-01T00:00:00",
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: MOCK_CUSTOMER
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_service():
    with patch("app.routers.reviews.review_service") as mock:
        yield mock


def test_submit_review_success(mock_service):
    mock_service.submit_review.return_value = MOCK_REVIEW_OUT
    response = client.post(
        "/reviews/",
        json={
            "order_id": str(ORDER_ID),
            "rating": 4,
            "tags": ["Delicious", "Fast delivery"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 4
    assert data["tags"] == ["Delicious", "Fast delivery"]
    assert data["order_id"] == str(ORDER_ID)


def test_submit_review_no_tags(mock_service):
    mock_service.submit_review.return_value = MOCK_REVIEW_OUT
    response = client.post(
        "/reviews/",
        json={"order_id": str(ORDER_ID), "rating": 5},
    )
    assert response.status_code == 201


def test_submit_review_invalid_rating():
    response = client.post(
        "/reviews/",
        json={"order_id": str(ORDER_ID), "rating": 6},
    )
    assert response.status_code == 422


def test_submit_review_invalid_tag():
    response = client.post(
        "/reviews/",
        json={"order_id": str(ORDER_ID), "rating": 3, "tags": ["InvalidTag"]},
    )
    assert response.status_code == 422


def test_submit_review_not_delivered(mock_service):
    mock_service.submit_review.side_effect = ValueError(
        "Reviews can only be submitted for delivered orders."
    )
    response = client.post(
        "/reviews/",
        json={"order_id": str(ORDER_ID), "rating": 3},
    )
    assert response.status_code == 400
    assert "delivered" in response.json()["detail"]


def test_submit_review_duplicate(mock_service):
    mock_service.submit_review.side_effect = ValueError(
        "A review already exists for order"
    )
    response = client.post(
        "/reviews/",
        json={"order_id": str(ORDER_ID), "rating": 5},
    )
    assert response.status_code == 400


def test_submit_review_wrong_customer(mock_service):
    mock_service.submit_review.side_effect = PermissionError(
        "You can only review your own orders."
    )
    response = client.post(
        "/reviews/",
        json={"order_id": str(ORDER_ID), "rating": 4},
    )
    assert response.status_code == 403


def test_owner_cannot_submit_review():
    app.dependency_overrides[get_current_user] = lambda: MOCK_OWNER
    response = client.post(
        "/reviews/",
        json={"order_id": str(ORDER_ID), "rating": 4},
    )
    assert response.status_code == 403
    assert "customers" in response.json()["detail"]
