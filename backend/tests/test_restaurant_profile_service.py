from unittest.mock import patch

import app.services.restaurant_service as service
import pytest
from app.schemas.kaggle import KaggleRestaurant
from app.schemas.restaurant_profile import RestaurantProfileOut, RestaurantProfileUpdate

RESTAURANT = KaggleRestaurant(restaurant_id="10", name="Kaggle Name")
PROFILE = RestaurantProfileOut(restaurant_id="10", name="Owner Name")


@pytest.fixture(autouse=True)
def mock_repos():
    with patch(
        "app.services.restaurant_service.kaggle_restaurant_repository"
    ) as mock_kag, patch(
        "app.services.restaurant_service.restaurant_profile_repository"
    ) as mock_prof:
        mock_kag.get_by_id.side_effect = lambda rid: RESTAURANT if rid == "10" else None
        mock_prof.get_by_id.return_value = None
        mock_prof.upsert.return_value = PROFILE
        yield mock_kag, mock_prof


# get_profile (profile exists in repo)
def test_get_profile_returns_owner_profile(mock_repos):
    _, mock_prof = mock_repos
    mock_prof.get_by_id.return_value = PROFILE
    result = service.get_profile("10")
    assert result.name == "Owner Name"


# get_profile (falls back to kaggle when no owner profile)
def test_get_profile_falls_back_to_kaggle(mock_repos):
    result = service.get_profile("10")
    assert result is not None
    assert result.name == "Kaggle Name"
    assert result.restaurant_id == "10"


# get_profile (unknown restaurant)
def test_get_profile_unknown_restaurant_returns_none():
    result = service.get_profile("999")
    assert result is None


# get_profile (owner profile takes priority over kaggle)
def test_get_profile_owner_profile_not_checked_against_kaggle(mock_repos):
    _, mock_prof = mock_repos
    mock_prof.get_by_id.return_value = PROFILE
    result = service.get_profile("10")
    assert result.name == "Owner Name"


# update_profile (success)
def test_update_profile_returns_updated(mock_repos):
    data = RestaurantProfileUpdate(name="New Name")
    result = service.update_profile("10", data)
    assert result is not None
    assert result.name == "Owner Name"


# update_profile (calls upsert with correct args)
def test_update_profile_calls_upsert(mock_repos):
    _, mock_prof = mock_repos
    data = RestaurantProfileUpdate(name="New Name")
    service.update_profile("10", data)
    mock_prof.upsert.assert_called_once_with("10", data, "Kaggle Name")


# update_profile (unknown restaurant)
def test_update_profile_unknown_restaurant_returns_none():
    data = RestaurantProfileUpdate(name="Whatever")
    result = service.update_profile("999", data)
    assert result is None


# update_profile (does not call upsert for unknown restaurant)
def test_update_profile_unknown_does_not_call_upsert(mock_repos):
    _, mock_prof = mock_repos
    service.update_profile("999", RestaurantProfileUpdate(name="X"))
    mock_prof.upsert.assert_not_called()
