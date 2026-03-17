import json
from unittest.mock import patch

import app.repositories.restaurant_profile_repository as repo
import pytest
from app.schemas.restaurant_profile import RestaurantProfileUpdate


@pytest.fixture(autouse=True)
def tmp_data(tmp_path):
    data_file = tmp_path / "restaurant_profiles.json"
    data_file.write_text("[]")
    with patch.object(repo, "DATA_PATH", str(data_file)):
        yield data_file


def test_get_by_id_not_found():
    assert repo.get_by_id("999") is None


def test_upsert_creates_new_profile():
    data = RestaurantProfileUpdate(name="My Restaurant")
    result = repo.upsert("10", data, "Default Name")
    assert result.restaurant_id == "10"
    assert result.name == "My Restaurant"


def test_upsert_uses_base_name_when_no_name_provided():
    data = RestaurantProfileUpdate()
    result = repo.upsert("10", data, "Default Name")
    assert result.name == "Default Name"


def test_upsert_updates_existing_profile():
    repo.upsert("10", RestaurantProfileUpdate(name="First"), "Base")
    result = repo.upsert("10", RestaurantProfileUpdate(name="Updated"), "Base")
    assert result.name == "Updated"


def test_upsert_only_creates_one_entry():
    repo.upsert("10", RestaurantProfileUpdate(name="First"), "Base")
    repo.upsert("10", RestaurantProfileUpdate(name="Second"), "Base")
    repo.upsert("10", RestaurantProfileUpdate(name="Third"), "Base")
    result = repo.get_by_id("10")
    assert result.name == "Third"


def test_get_by_id_returns_profile():
    repo.upsert("10", RestaurantProfileUpdate(name="Pizza Place"), "Base")
    result = repo.get_by_id("10")
    assert result is not None
    assert result.name == "Pizza Place"


def test_multiple_restaurants_independent():
    repo.upsert("10", RestaurantProfileUpdate(name="Restaurant A"), "Base A")
    repo.upsert("20", RestaurantProfileUpdate(name="Restaurant B"), "Base B")
    assert repo.get_by_id("10").name == "Restaurant A"
    assert repo.get_by_id("20").name == "Restaurant B"
