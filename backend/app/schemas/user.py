from pydantic import BaseModel, EmailStr, Field
from typing import Literal 
from uuid import UUID

Role = Literal["customer", "owner", "admin"]

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    role: Role = "customer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str 

class UserPublic(BaseModel):
    id: UUID
    email: EmailStr
    role: Role

class UserInDB(UserPublic):
    password_hash: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
