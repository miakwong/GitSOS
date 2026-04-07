# Feat9 — Review endpoints
from uuid import UUID

from app.dependencies import get_current_user
from app.schemas.constants import ROLE_CUSTOMER
from app.schemas.review import RestaurantRatingSummary, ReviewCreate, ReviewOut
from app.schemas.user import UserInDB
from app.services import review_service
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", response_model=ReviewOut, status_code=201)
def submit_review(
    payload: ReviewCreate,
    current_user: UserInDB = Depends(get_current_user),
) -> ReviewOut:
    if current_user.role != ROLE_CUSTOMER:
        raise HTTPException(
            status_code=403, detail="Only customers can submit reviews."
        )
    try:
        return review_service.submit_review(payload, str(current_user.id))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/restaurant/{restaurant_id}", response_model=RestaurantRatingSummary)
def get_restaurant_ratings(
    restaurant_id: int,
    current_user: UserInDB = Depends(get_current_user),
) -> RestaurantRatingSummary:
    return review_service.get_restaurant_ratings(restaurant_id)


@router.delete("/{review_id}", status_code=204)
def delete_review(
    review_id: UUID,
    current_user: UserInDB = Depends(get_current_user),
) -> None:
    try:
        review_service.delete_review(review_id, str(current_user.id), current_user.role)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
