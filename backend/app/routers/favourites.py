from uuid import UUID

from app.dependencies import get_current_user
from app.schemas.constants import ROLE_CUSTOMER
from app.schemas.favourite import FavouriteCreate, FavouriteOut
from app.schemas.order import Order
from app.schemas.user import UserInDB
from app.services import favourite_service
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/favourites", tags=["favourites"])


@router.post("/", response_model=FavouriteOut, status_code=status.HTTP_201_CREATED)
def add_favourite(
    payload: FavouriteCreate,
    current_user: UserInDB = Depends(get_current_user),
) -> FavouriteOut:
    if current_user.role != ROLE_CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can save favourites.",
        )
    return favourite_service.add_favourite(payload, str(current_user.id))


@router.get("/", response_model=list[FavouriteOut])
def list_favourites(
    current_user: UserInDB = Depends(get_current_user),
) -> list[FavouriteOut]:
    if current_user.role != ROLE_CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can view favourites.",
        )
    return favourite_service.get_favourites(str(current_user.id))


@router.post(
    "/{favourite_id}/reorder",
    response_model=Order,
    status_code=status.HTTP_201_CREATED,
    summary="Reorder from a saved favourite",
    description="Creates a new order using the same details from a saved favourite order.",
)
def reorder_from_favourite(
    favourite_id: UUID,
    current_user: UserInDB = Depends(get_current_user),
) -> Order:
    if current_user.role != ROLE_CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can reorder from favourites.",
        )
    return favourite_service.reorder_from_favourite(favourite_id, str(current_user.id))


@router.delete("/{favourite_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favourite(
    favourite_id: UUID,
    current_user: UserInDB = Depends(get_current_user),
) -> None:
    if current_user.role != ROLE_CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can remove favourites.",
        )
    favourite_service.remove_favourite(favourite_id, str(current_user.id))
