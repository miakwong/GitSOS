from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService, TOKEN_BLACKLIST


SECRET_KEY = "dev-secret-key-for-gitsos-project-authentication-12345"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_user_repo() -> UserRepository:
    users_file = Path(__file__).resolve().parent / "data" / "users.json"
    return UserRepository(users_file)


def get_auth_service(user_repo: UserRepository = Depends(get_user_repo)) -> AuthService:
    return AuthService(
        user_repo=user_repo,
        secret_key=SECRET_KEY,
        algorithm=ALGORITHM,
    )

def get_current_token(token: str = Depends(oauth2_scheme)) -> str:
    return token

def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repo),
):
    if token in TOKEN_BLACKLIST:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated",
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# Check that the token belongs to an admin user
def get_current_admin(
    token: str = Depends(oauth2_scheme),
) -> UUID:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to administrators",
        )
    return UUID(payload["sub"])


def get_current_owner(
    token: str = Depends(oauth2_scheme),
) -> tuple[UUID, int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    if payload.get("role") != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to restaurant owners",
        )
    rest_id: Optional[int] = payload.get("restaurant_id")
    if rest_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner account has no associated restaurant",
        )
    return UUID(payload["sub"]), rest_id
