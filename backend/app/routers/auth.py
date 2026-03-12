from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_auth_service, get_current_user, get_current_token
from app.schemas.user import UserCreate, UserLogin, UserPublic, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
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
def me(current_user = Depends(get_current_user)):
    return UserPublic(
        id=current_user.id, 
        email=current_user.email, 
        role=current_user.role,
    )