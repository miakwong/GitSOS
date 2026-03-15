from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, model_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Literal["customer", "owner", "admin"]
    restaurant_id: Optional[int] = None

    @model_validator(mode="after")
    def check_owner_restaurant(self) -> "UserCreate":
        if self.role == "owner" and self.restaurant_id is None:
            raise ValueError("restaurant_id is required for owner accounts")
        if self.role != "owner" and self.restaurant_id is not None:
            raise ValueError("restaurant_id is only valid for owner accounts")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    password_hash: str
    restaurant_id: Optional[int] = None


class UserPublic(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    restaurant_id: Optional[int] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# extends public user info with role-specific data
class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    restaurant_id: Optional[int] = None
    # role == "customer"
    order_count: Optional[int] = None
    order_history: Optional[List[str]] = None
