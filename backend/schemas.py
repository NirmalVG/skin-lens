from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    """Schema for user registration requests."""
    email: EmailStr
    password: str
    name: Optional[str] = None
    skin_type: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login requests."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token responses."""
    access_token: str
    token_type: str = "bearer"
    user: dict
