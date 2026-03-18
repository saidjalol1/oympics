"""
Authentication request and response schemas.

This module defines Pydantic models for authentication-related API requests
and responses, including registration, login, email verification, and error handling.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    """
    Request schema for user registration.
    
    Attributes:
        email: Valid email address for the new user account
        password: Password with minimum 8 characters and maximum 72 bytes
    """
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be 8-72 characters (max 72 bytes UTF-8)")
    
    @field_validator('password')
    @classmethod
    def validate_password_bytes(cls, v: str) -> str:
        """Validate that password doesn't exceed 72 bytes when UTF-8 encoded."""
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot exceed 72 bytes when UTF-8 encoded')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "securepass123"
            }
        }
    )


class LoginRequest(BaseModel):
    """
    Request schema for user login.
    
    Attributes:
        email: Email address of the user
        password: User's password
    """
    email: EmailStr
    password: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "securepass123"
            }
        }
    )


class VerifyEmailRequest(BaseModel):
    """
    Request schema for email verification.
    
    Attributes:
        token: JWT token sent via email for verification
    """
    token: str = Field(min_length=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )


class UserResponse(BaseModel):
    """
    Response schema for user data.
    
    Attributes:
        id: Unique user identifier
        email: User's email address
        is_verified: Whether the user's email has been verified
        is_admin: Whether the user is an admin
        created_at: Timestamp when the user account was created
    """
    id: int
    email: str
    is_verified: bool
    is_admin: bool
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "is_verified": True,
                "is_admin": True,
                "created_at": "2024-01-15T10:30:00"
            }
        }
    )


class AuthResponse(BaseModel):
    """
    Response schema for authentication operations.
    
    Attributes:
        message: Localized message describing the operation result
        user: Optional user data (included on successful login/verification)
    """
    message: str
    user: Optional[UserResponse] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Login successful",
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "is_verified": True,
                    "is_admin": True,
                    "created_at": "2024-01-15T10:30:00"
                }
            }
        }
    )


class ErrorResponse(BaseModel):
    """
    Response schema for error messages.
    
    Attributes:
        detail: Localized error message describing what went wrong
    """
    detail: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Invalid credentials"
            }
        }
    )
