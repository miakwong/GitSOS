# Feat7 — Data access layer for payments
import json
import os
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.schemas.payment import PaymentRecord

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/payments.json")

# helpers


def _load() -> list[dict]:
    """Load all payment records from JSON file"""
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(records: list[dict]) -> None:
    """Save all payment records to JSON file."""
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def _record_to_dict(record: PaymentRecord) -> dict:
    """Convert PaymentRecord to JSON file(UUID → str)."""
    return {
        "payment_id": str(record.payment_id),
        "order_id": str(record.order_id),
        "customer_id": str(record.customer_id),
        "status": record.status,
        "amount": record.amount,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _dict_to_record(data: dict) -> PaymentRecord:
    """Convert dict from JSON into PaymentRecord (str → UUID)."""
    return PaymentRecord(
        payment_id=UUID(data["payment_id"]),
        order_id=UUID(data["order_id"]),
        customer_id=UUID(data["customer_id"]),
        status=data["status"],
        amount=data["amount"],
        created_at=data["created_at"],
        updated_at=data.get("updated_at"),
    )


def create(record: PaymentRecord) -> PaymentRecord:
    """Add a new PaymentRecord to the repository and persist to file."""
    records = _load()
    records.append(_record_to_dict(record))
    _save(records)
    return record


def get_by_id(payment_id: UUID) -> Optional[PaymentRecord]:
    for data in _load():
        if data["payment_id"] == str(payment_id):
            return _dict_to_record(data)
    return None


def get_by_order_id(order_id: UUID) -> Optional[PaymentRecord]:
    """Find a payment record by its associated order_id. Returns None if not found."""
    for data in _load():
        if data["order_id"] == str(order_id):
            return _dict_to_record(data)
    return None


def list_all() -> list[PaymentRecord]:
    """Return all payment records. Used by admin endpoints."""
    return [_dict_to_record(data) for data in _load()]


def update_status(order_id: UUID, new_status: str) -> Optional[PaymentRecord]:
    """Update the status of a payment record by order_id. Returns the Updated record, or None if the order is not found."""
    records = _load()
    for record in records:
        if record["order_id"] == str(order_id):
            record["status"] = new_status
            record["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save(records)
            return _dict_to_record(record)
    return None
