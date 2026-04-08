from uuid import UUID

from app.dependencies import get_current_user
from app.schemas.constants import ROLE_CUSTOMER
from app.schemas.favourite import FavouriteCreate, FavouriteOut, PopularItemOut
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


@router.get(
    "/analytics/popular",
    response_model=list[PopularItemOut],
    summary="Get popular favourited menu items",
    description="Returns menu items sorted by how often they are favourited. Owners see their restaurant only, admins see all.",
)
def get_popular_items(
    current_user: UserInDB = Depends(get_current_user),
) -> list[PopularItemOut]:
    if current_user.role == ROLE_CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot access favourite analytics.",
        )

    if current_user.role == "owner":
        return favourite_service.get_popular_items(restaurant_id=current_user.restaurant_id)

    return favourite_service.get_popular_items()


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
