import json
import os
from typing import Optional
from uuid import UUID

from app.schemas.favourite import FavouriteRecord

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/favourites.json")


def _load() -> list[dict]:
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(records: list[dict]) -> None:
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def _record_to_dict(record: FavouriteRecord) -> dict:
    return {
        "favourite_id": str(record.favourite_id),
        "order_id": str(record.order_id),
        "customer_id": str(record.customer_id),
        "created_at": record.created_at,
    }


def _dict_to_record(data: dict) -> FavouriteRecord:
    return FavouriteRecord(
        favourite_id=UUID(data["favourite_id"]),
        order_id=UUID(data["order_id"]),
        customer_id=UUID(data["customer_id"]),
        created_at=data["created_at"],
    )


def create(record: FavouriteRecord) -> FavouriteRecord:
    records = _load()
    records.append(_record_to_dict(record))
    _save(records)
    return record


def get_by_customer(customer_id: UUID) -> list[FavouriteRecord]:
    return [
        _dict_to_record(d)
        for d in _load()
        if d["customer_id"] == str(customer_id)
    ]


def get_by_id(favourite_id: UUID) -> Optional[FavouriteRecord]:
    for data in _load():
        if data["favourite_id"] == str(favourite_id):
            return _dict_to_record(data)
    return None


def exists(customer_id: UUID, order_id: UUID) -> bool:
    for data in _load():
        if data["customer_id"] == str(customer_id) and data["order_id"] == str(order_id):
            return True
    return False


def delete(favourite_id: UUID) -> bool:
    records = _load()
    filtered = [d for d in records if d["favourite_id"] != str(favourite_id)]
    if len(filtered) == len(records):
        return False
    _save(filtered)
    return True
