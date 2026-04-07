from datetime import datetime, timezone
from typing import List
from uuid import UUID

from app.schemas.constants import VALID_REVIEW_TAGS
from pydantic import BaseModel, Field, field_validator


class ReviewCreate(BaseModel):
    order_id: UUID = Field(..., description="System-created order ID (UUID)")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    tags: List[str] = Field(
        default_factory=list,
        description=f"Optional preset tags. Allowed values: {VALID_REVIEW_TAGS}",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        invalid = [t for t in v if t not in VALID_REVIEW_TAGS]
        if invalid:
            raise ValueError(f"Invalid tag(s): {invalid}. Allowed: {VALID_REVIEW_TAGS}")
        return v


class ReviewRecord(BaseModel):
    review_id: UUID = Field(..., description="Unique review ID (UUID)")
    order_id: UUID = Field(..., description="Linked system order ID (UUID)")
    customer_id: UUID = Field(
        ..., description="ID of the customer who submitted the review"
    )
    restaurant_id: int = Field(..., description="Restaurant being reviewed")
    rating: int = Field(..., ge=1, le=5)
    tags: List[str] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of review creation",
    )


class RestaurantRatingSummary(BaseModel):
    restaurant_id: int
    review_count: int
    average_rating: float
    tag_counts: dict
    reviews: List["ReviewOut"]


class ReviewOut(BaseModel):
    review_id: str
    order_id: str
    customer_id: str
    restaurant_id: int
    rating: int
    tags: List[str]
    created_at: str

    @classmethod
    def from_record(cls, record: ReviewRecord) -> "ReviewOut":
        return cls(
            review_id=str(record.review_id),
            order_id=str(record.order_id),
            customer_id=str(record.customer_id),
            restaurant_id=record.restaurant_id,
            rating=record.rating,
            tags=record.tags,
            created_at=record.created_at,
        )
