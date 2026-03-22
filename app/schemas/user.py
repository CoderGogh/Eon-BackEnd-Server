from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MANAGER = "manager"


class UserBase(BaseModel):
    username: str = Field(..., max_length=50, example="admin_user")
    email: Optional[str] = Field(None, example="admin@codyssey.com")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: UserRole = Field(UserRole.USER, description="기본값은 일반 사용자(user)입니다.")


class UserInDB(UserBase):
    id: int
    role: UserRole
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None


class Login(BaseModel):
    username: str
    password: str
