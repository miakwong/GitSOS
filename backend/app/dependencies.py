from pathlib import Path
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_user_repo() -> UserRepository:
    users_file = Path(__file__).resolve().parent / "data" / "users.json"
    return UserRepository(users_file)


def get_auth_service(user_repo: UserRepository = Depends(get_user_repo)) -> AuthService:
    return AuthService(user_repo=user_repo, secret_key="CHANGE_ME")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repo),
) -> UUID:
    try:
        payload = jwt.decode(token, "CHANGE_ME", algorithms=["HS256"])
        return UUID(payload["sub"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )