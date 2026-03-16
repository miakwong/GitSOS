from datetime import datetime, timezone
from uuid import UUID

from app.schemas.constants import VALID_NOTIFICATION_TYPES
from pydantic import BaseModel, Field


class NotificationRecord(BaseModel):
    notification_id: UUID
    user_id: UUID
    order_id: UUID
    type: str = Field(..., description=f"One of: {VALID_NOTIFICATION_TYPES}")
    message: str
    is_read: bool = False
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class NotificationOut(BaseModel):
    notification_id: str
    user_id: str
    order_id: str
    type: str
    message: str
    is_read: bool
    created_at: str

    @classmethod
    def from_record(cls, record: NotificationRecord) -> "NotificationOut":
        return cls(
            notification_id=str(record.notification_id),
            user_id=str(record.user_id),
            order_id=str(record.order_id),
            type=record.type,
            message=record.message,
            is_read=record.is_read,
            created_at=record.created_at,
        )
