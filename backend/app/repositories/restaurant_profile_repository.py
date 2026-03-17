import json
import os
from typing import Optional

from app.schemas.restaurant_profile import RestaurantProfileOut, RestaurantProfileUpdate

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/restaurant_profiles.json")


def _load() -> list[dict]:
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(profiles: list[dict]) -> None:
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)


def get_by_id(restaurant_id: str) -> Optional[RestaurantProfileOut]:
    for profile in _load():
        if profile["restaurant_id"] == restaurant_id:
            return RestaurantProfileOut(**profile)
    return None


def upsert(restaurant_id: str, data: RestaurantProfileUpdate, base_name: str) -> RestaurantProfileOut:
    profiles = _load()
    for profile in profiles:
        if profile["restaurant_id"] == restaurant_id:
            if data.name is not None:
                profile["name"] = data.name
            _save(profiles)
            return RestaurantProfileOut(**profile)
    new_profile = {
        "restaurant_id": restaurant_id,
        "name": data.name if data.name is not None else base_name,
    }
    profiles.append(new_profile)
    _save(profiles)
    return RestaurantProfileOut(**new_profile)
