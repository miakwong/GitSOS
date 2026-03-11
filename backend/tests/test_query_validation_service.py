import pytest
from fastapi import HTTPException

from app.services.query_validation_service import QueryValidationService


def test_reject_unsupported_filters_raises_http_400():
    provided_params = {
        "city": "Kelowna",
        "bad_filter": "oops",
    }
    allowed_filters = {"city", "cuisine", "restaurant_name"}

    with pytest.raises(HTTPException) as exc_info:
        QueryValidationService.reject_unsupported_filters(
            provided_params=provided_params,
            allowed_filters=allowed_filters,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["message"] == "Unsupported query parameter(s)."
    assert "bad_filter" in exc_info.value.detail["unsupported"]


def test_reject_unsupported_filters_allows_valid_params():
    provided_params = {
        "city": "Kelowna",
        "cuisine": "Japanese",
    }
    allowed_filters = {"city", "cuisine", "restaurant_name"}

    # Should not raise any exception
    QueryValidationService.reject_unsupported_filters(
        provided_params=provided_params,
        allowed_filters=allowed_filters,
    )


def test_validate_price_range_raises_http_400():
    with pytest.raises(HTTPException) as exc_info:
        QueryValidationService.validate_price_range(
            min_price=50,
            max_price=10,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["message"] == "Invalid price range."


def test_validate_price_range_accepts_valid_range():
    QueryValidationService.validate_price_range(
        min_price=10,
        max_price=50,
    )


def test_validate_order_value_range_raises_http_400():
    with pytest.raises(HTTPException) as exc_info:
        QueryValidationService.validate_order_value_range(
            min_order_value=100,
            max_order_value=20,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["message"] == "Invalid order value range."


def test_validate_order_value_range_accepts_valid_range():
    QueryValidationService.validate_order_value_range(
        min_order_value=20,
        max_order_value=100,
    )