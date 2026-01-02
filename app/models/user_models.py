"""
User models for authentication system.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with email."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserLogin(UserBase):
    """Schema for user login."""
    password: str


class User(UserBase):
    """User schema returned to client (no password)."""
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserInDB(User):
    """User schema as stored in database."""
    hashed_password: str


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    email: Optional[str] = None
    user_id: Optional[str] = None
