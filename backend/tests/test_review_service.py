import uuid
from unittest.mock import patch

import app.services.review_service as service
import pytest
from app.schemas.review import ReviewRecord

RESTAURANT_ID = 5
CUSTOMER_ID = uuid.uuid4()
ORDER_ID = uuid.uuid4()


def _make_record(rating: int, tags=None) -> ReviewRecord:
    return ReviewRecord(
        review_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        customer_id=CUSTOMER_ID,
        restaurant_id=RESTAURANT_ID,
        rating=rating,
        tags=tags or [],
    )


# -------------------------
# get_restaurant_ratings
# -------------------------


@pytest.fixture
def mock_repo():
    with patch("app.services.review_service.review_repository") as mock:
        yield mock


def test_get_restaurant_ratings_no_reviews(mock_repo):
    mock_repo.get_by_restaurant_id.return_value = []
    result = service.get_restaurant_ratings(RESTAURANT_ID)
    assert result.review_count == 0
    assert result.average_rating == 0.0
    assert result.tag_counts == {}
    assert result.reviews == []


def test_get_restaurant_ratings_single_review(mock_repo):
    mock_repo.get_by_restaurant_id.return_value = [_make_record(4)]
    result = service.get_restaurant_ratings(RESTAURANT_ID)
    assert result.review_count == 1
    assert result.average_rating == 4.0


def test_get_restaurant_ratings_average_rounded(mock_repo):
    # 4+4+3 = 11/3 = 3.666... → rounds to 3.67
    mock_repo.get_by_restaurant_id.return_value = [
        _make_record(4),
        _make_record(4),
        _make_record(3),
    ]
    result = service.get_restaurant_ratings(RESTAURANT_ID)
    assert result.review_count == 3
    assert result.average_rating == 3.67


def test_get_restaurant_ratings_average_two_decimals(mock_repo):
    mock_repo.get_by_restaurant_id.return_value = [
        _make_record(4),
        _make_record(3),
    ]
    result = service.get_restaurant_ratings(RESTAURANT_ID)
    assert result.average_rating == 3.5


def test_get_restaurant_ratings_tag_counts(mock_repo):
    mock_repo.get_by_restaurant_id.return_value = [
        _make_record(5, tags=["Delicious", "Fast delivery"]),
        _make_record(4, tags=["Delicious"]),
        _make_record(3, tags=[]),
    ]
    result = service.get_restaurant_ratings(RESTAURANT_ID)
    assert result.tag_counts["Delicious"] == 2
    assert result.tag_counts["Fast delivery"] == 1
    assert "Just okay" not in result.tag_counts


def test_get_restaurant_ratings_reviews_included(mock_repo):
    mock_repo.get_by_restaurant_id.return_value = [
        _make_record(5, tags=["Delicious"]),
        _make_record(2, tags=["Overpriced"]),
    ]
    result = service.get_restaurant_ratings(RESTAURANT_ID)
    assert len(result.reviews) == 2
    ratings = {r.rating for r in result.reviews}
    assert ratings == {5, 2}


def test_get_restaurant_ratings_correct_restaurant_id(mock_repo):
    mock_repo.get_by_restaurant_id.return_value = []
    result = service.get_restaurant_ratings(RESTAURANT_ID)
    assert result.restaurant_id == RESTAURANT_ID
