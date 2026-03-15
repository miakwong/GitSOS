from typing import List
from uuid import UUID

from app.dependencies import (
    get_auth_service,
    get_current_token,
    get_current_user,
    get_order_service,
    get_user_repo,
    require_role,
)
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserProfile, UserPublic
from app.services.auth_service import AuthService
from app.services.order_service import OrderService
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
def register(payload: UserCreate, auth: AuthService = Depends(get_auth_service)):
    try:
        user = auth.register_user(payload)
        return UserPublic(id=user.id, email=user.email, role=user.role)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, auth: AuthService = Depends(get_auth_service)):
    try:
        token = auth.login_user(payload)
        return TokenResponse(access_token=token, token_type="bearer")
    except PermissionError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/logout")
def logout(
    token: str = Depends(get_current_token),
    auth: AuthService = Depends(get_auth_service),
):
    auth.logout_token(token)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserPublic)
def me(current_user=Depends(get_current_user)):
    return UserPublic(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
    )


def _build_profile(user, orders=None) -> UserProfile:
    profile = UserProfile(
        id=user.id,
        email=user.email,
        role=user.role,
        restaurant_id=user.restaurant_id,
    )
    if user.role == "customer":
        order_list = orders or []
        profile.order_count = len(order_list)
        profile.order_history = [str(o.order_id) for o in order_list]
    return profile


# returns the authenticated user
@router.get("/profile", response_model=UserProfile)
def get_profile(
    current_user=Depends(get_current_user),
    order_svc: OrderService = Depends(get_order_service),
):
    orders = None
    if current_user.role == "customer":
        orders = order_svc.get_orders_by_customer(str(current_user.id))
    return _build_profile(current_user, orders)


# returns a profile by user ID - admin can view any user, others only their own
@router.get("/users/{user_id}/profile", response_model=UserProfile)
def get_user_profile(
    user_id: UUID,
    current_user=Depends(get_current_user),
    order_svc: OrderService = Depends(get_order_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you can only view your own profile",
        )
    # admin viewing another user - look them up
    if current_user.id != user_id:
        target = user_repo.get_user_by_id(user_id)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    else:
        target = current_user
    orders = None
    if target.role == "customer":
        orders = order_svc.get_orders_by_customer(str(target.id))
    return _build_profile(target, orders)


# admin only - returns all users and their roles
@router.get(
    "/admin/users",
    response_model=List[UserPublic],
    dependencies=[Depends(require_role("admin"))],
)
def admin_list_users(user_repo: UserRepository = Depends(get_user_repo)):
    return [
        UserPublic(id=u.id, email=u.email, role=u.role) for u in user_repo.list_users()
    ]
