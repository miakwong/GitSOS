from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.user import UserCreate, UserLogin, UserPublic, TokenResponse
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, auth: AuthService = Depends(get_auth_service)):
    try:
        user = auth.register(payload)
        return UserPublic(id=user.id, email=user.email, role=user.role)
    except ValueError:
        raise HTTPException(status_code=409, detail="Email already registered")


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, auth: AuthService = Depends(get_auth_service)):
    try:
        token = auth.login(payload)
        return TokenResponse(access_token=token)
    except PermissionError:
        raise HTTPException(status_code=401, detail="Invalid credentials")