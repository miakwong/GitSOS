# Feat9 — Review endpoints
from app.dependencies import get_current_user
from app.schemas.constants import ROLE_CUSTOMER
from app.schemas.review import ReviewCreate, ReviewOut
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
