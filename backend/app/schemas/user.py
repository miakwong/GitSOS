from pydantic import BaseModel, EmailStr
from typing import Literal 
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str 
    role: Literal["customer", "owner", "admin"]

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    password_hash: str

class UserPublic(BaseModel):
    id: UUID
    email: EmailStr  
    role: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
