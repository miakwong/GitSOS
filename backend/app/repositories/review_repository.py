# Feat9 — Data access layer for reviews
import json
import os
from typing import List, Optional
from uuid import UUID

from app.schemas.review import ReviewRecord

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/reviews.json")


def _load() -> list[dict]:
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(records: list[dict]) -> None:
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def _record_to_dict(record: ReviewRecord) -> dict:
    return {
        "review_id": str(record.review_id),
        "order_id": str(record.order_id),
        "customer_id": str(record.customer_id),
        "restaurant_id": record.restaurant_id,
        "rating": record.rating,
        "tags": record.tags,
        "created_at": record.created_at,
    }


def _dict_to_record(data: dict) -> ReviewRecord:
    return ReviewRecord(
        review_id=UUID(data["review_id"]),
        order_id=UUID(data["order_id"]),
        customer_id=UUID(data["customer_id"]),
        restaurant_id=data["restaurant_id"],
        rating=data["rating"],
        tags=data.get("tags", []),
        created_at=data["created_at"],
    )


def create(record: ReviewRecord) -> ReviewRecord:
    records = _load()
    records.append(_record_to_dict(record))
    _save(records)
    return record


def get_by_order_id(order_id: UUID) -> Optional[ReviewRecord]:
    for data in _load():
        if data["order_id"] == str(order_id):
            return _dict_to_record(data)
    return None


def get_by_restaurant_id(restaurant_id: int) -> List[ReviewRecord]:
    return [_dict_to_record(d) for d in _load() if d["restaurant_id"] == restaurant_id]


def list_all() -> List[ReviewRecord]:
    return [_dict_to_record(d) for d in _load()]
