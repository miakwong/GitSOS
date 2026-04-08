from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field


class FavouriteCreate(BaseModel):
    order_id: UUID = Field(..., description="ID of the system order to save as favourite")


class FavouriteRecord(BaseModel):
    favourite_id: UUID = Field(..., description="Unique ID for this favourite entry")
    order_id: UUID = Field(..., description="ID of the saved order")
    customer_id: UUID = Field(..., description="ID of the customer who saved this favourite")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp when the favourite was created",
    )


class FavouriteOut(BaseModel):
    favourite_id: str
    order_id: str
    customer_id: str
    created_at: str

    @classmethod
    def from_record(cls, record: FavouriteRecord) -> "FavouriteOut":
        return cls(
            favourite_id=str(record.favourite_id),
            order_id=str(record.order_id),
            customer_id=str(record.customer_id),
            created_at=record.created_at,
        )
