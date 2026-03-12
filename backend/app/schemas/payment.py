from datetime import datetime
from typing import Optional
from uuid import UUID

from app.schemas.constants import (
    PAYMENT_STATUS_PENDING,
    VALID_PAYMENT_STATUSES,
)
from pydantic import BaseModel, Field, field_validator


# PaymentCreate
class PaymentCreate(BaseModel):
    order_id: UUID = Field(..., description="System-created order ID (UUID)")


# PaymentRecord
# stored in payments.json
class PaymentRecord(BaseModel):
    payment_id: UUID = Field(..., description="Unique payment ID (UUID)")
    order_id: UUID = Field(..., description="Linked system order ID (UUID)")
    customer_id: UUID = Field(..., description="ID of the customer who paid (UUID)")
    status: str = Field(
        default=PAYMENT_STATUS_PENDING,
        description=f"One of: {VALID_PAYMENT_STATUSES}",
    )
    amount: float = Field(..., gt=0, description="Total amount charged")
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp of payment creation",
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of last status update",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_PAYMENT_STATUSES:
            raise ValueError(
                f"Invalid status '{v}'. Must be one of: {VALID_PAYMENT_STATUSES}"
            )
        return v


# PaymentOut -- API response
# UUID fields serialized as str for JSON
class PaymentOut(BaseModel):
    payment_id: str
    order_id: str
    customer_id: str
    status: str
    amount: float
    created_at: str
    updated_at: Optional[str] = None

    @classmethod
    def from_record(cls, record: PaymentRecord) -> "PaymentOut":
        return cls(
            payment_id=str(record.payment_id),
            order_id=str(record.order_id),
            customer_id=str(record.customer_id),
            status=record.status,
            amount=record.amount,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
