from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

import jwt
from passlib.context import CryptContext

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLogin, UserInDB


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_minutes: int = 60,
    ):
        self.user_repo = user_repo
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_minutes = access_token_minutes
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password[:72])
    
    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        return self.pwd_context.verify(plain_password[:72], password_hash)

    def create_access_token(self, user_id: UUID, role: str) -> str:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=self.access_token_minutes)
        payload = {"sub": str(user_id), "role": role, "exp": exp}
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def register_user(self, user_create: UserCreate) -> UserInDB:
        if self.user_repo.get_user_by_email(user_create.email):
            raise ValueError("Email already registered")

        new_user = UserInDB(
            id=uuid4(),
            email=user_create.email,
            role=user_create.role,
            password_hash=self.hash_password(user_create.password),
        )
        return self.user_repo.create_user(new_user)

    def login_user(self, user_login: UserLogin) -> str:
        user = self.user_repo.get_user_by_email(user_login.email)
        if not user:
            raise PermissionError("Invalid credentials")

        if not self.verify_password(user_login.password, user.password_hash):
            raise PermissionError("Invalid credentials")

        return self.create_access_token(user.id, user.role)

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.PyJWTError:
            return None