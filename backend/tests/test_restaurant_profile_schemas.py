import pytest
from app.schemas.restaurant_profile import RestaurantProfileOut, RestaurantProfileUpdate
from pydantic import ValidationError

# tests
def test_profile_update_valid_name():
    data = RestaurantProfileUpdate(name="New Name")
    assert data.name == "New Name"


def test_profile_update_none_name():
    data = RestaurantProfileUpdate()
    assert data.name is None


def test_profile_update_empty_name_raises():
    with pytest.raises(ValidationError):
        RestaurantProfileUpdate(name="")


def test_profile_update_whitespace_name_raises():
    with pytest.raises(ValidationError):
        RestaurantProfileUpdate(name="   ")


def test_profile_out_valid():
    out = RestaurantProfileOut(restaurant_id="10", name="Test Restaurant")
    assert out.restaurant_id == "10"
    assert out.name == "Test Restaurant"
