import json
import os
from typing import Optional
from uuid import UUID

from app.schemas.notification import NotificationRecord

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/notifications.json")


def _load() -> list[dict]:
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(records: list[dict]) -> None:
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def _record_to_dict(record: NotificationRecord) -> dict:
    return {
        "notification_id": str(record.notification_id),
        "user_id": str(record.user_id),
        "order_id": str(record.order_id),
        "type": record.type,
        "message": record.message,
        "is_read": record.is_read,
        "created_at": record.created_at,
    }


def _dict_to_record(data: dict) -> NotificationRecord:
    return NotificationRecord(
        notification_id=UUID(data["notification_id"]),
        user_id=UUID(data["user_id"]),
        order_id=UUID(data["order_id"]),
        type=data["type"],
        message=data["message"],
        is_read=data["is_read"],
        created_at=data["created_at"],
    )


def create(record: NotificationRecord) -> NotificationRecord:
    records = _load()
    records.append(_record_to_dict(record))
    _save(records)
    return record


def get_by_id(notification_id: UUID) -> Optional[NotificationRecord]:
    for data in _load():
        if data["notification_id"] == str(notification_id):
            return _dict_to_record(data)
    return None


def list_by_user(user_id: UUID) -> list[NotificationRecord]:
    return [_dict_to_record(d) for d in _load() if d["user_id"] == str(user_id)]


def list_all() -> list[NotificationRecord]:
    return [_dict_to_record(d) for d in _load()]


def update_read_status(
    notification_id: UUID, is_read: bool
) -> Optional[NotificationRecord]:
    records = _load()
    for data in records:
        if data["notification_id"] == str(notification_id):
            data["is_read"] = is_read
            _save(records)
            return _dict_to_record(data)
    return None
