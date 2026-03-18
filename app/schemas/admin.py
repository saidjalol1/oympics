"""
Admin panel request and response schemas.

This module defines Pydantic models for admin-specific API requests and responses,
including user creation, updates, listing, and admin action responses.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class AdminCreateUserRequest(BaseModel):
    """
    Request schema for admin creating a new user.
    
    Allows administrators to create user accounts directly with optional
    email verification bypass and admin role assignment.
    
    Attributes:
        email: Valid email address for the new user account
        password: Password with minimum 8 characters and maximum 100 characters
        is_verified: Whether the user's email is pre-verified (admin bypass)
        is_admin: Whether the user should have admin privileges
    """
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=100,
        description="Password must be 8-100 characters"
    )
    is_verified: bool = Field(
        default=False,
        description="Whether the user's email is pre-verified"
    )
    is_admin: bool = Field(
        default=False,
        description="Whether the user should have admin privileges"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password_bytes(cls, v: str) -> str:
        """Validate that password doesn't exceed 100 bytes when UTF-8 encoded."""
        if len(v.encode('utf-8')) > 100:
            raise ValueError('Password cannot exceed 100 bytes when UTF-8 encoded')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newuser@example.com",
                "password": "securepass123",
                "is_verified": True,
                "is_admin": False
            }
        }
    )


class AdminUpdateUserRequest(BaseModel):
    """
    Request schema for admin updating an existing user.
    
    Allows administrators to update user details with partial field updates.
    All fields are optional - only specified fields will be updated.
    
    Attributes:
        email: New email address (optional)
        password: New password (optional, 8-100 characters if provided)
        is_verified: New verification status (optional)
        is_admin: New admin status (optional)
    """
    email: Optional[EmailStr] = Field(
        default=None,
        description="New email address"
    )
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=100,
        description="New password (8-100 characters if provided)"
    )
    is_verified: Optional[bool] = Field(
        default=None,
        description="New verification status"
    )
    is_admin: Optional[bool] = Field(
        default=None,
        description="New admin status"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password_bytes(cls, v: Optional[str]) -> Optional[str]:
        """Validate that password doesn't exceed 100 bytes when UTF-8 encoded."""
        if v is not None and len(v.encode('utf-8')) > 100:
            raise ValueError('Password cannot exceed 100 bytes when UTF-8 encoded')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "updated@example.com",
                "is_verified": True
            }
        }
    )


class UserListQueryParams(BaseModel):
    """
    Query parameters for user list endpoint.
    
    Supports pagination, email search filtering, verification status filtering,
    and admin status filtering.
    
    Attributes:
        skip: Number of records to skip for pagination (default: 0)
        limit: Maximum number of records to return (default: 50, max: 100)
        search: Optional email search filter (case-insensitive partial match)
        verified_only: Optional filter for verification status
        is_admin: Optional filter for admin status
    """
    skip: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip for pagination"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of records to return (1-100)"
    )
    search: Optional[str] = Field(
        default=None,
        description="Email search filter (case-insensitive partial match)"
    )
    verified_only: Optional[bool] = Field(
        default=None,
        description="Filter by verification status (True/False/None)"
    )
    is_admin: Optional[bool] = Field(
        default=None,
        description="Filter by admin status (True/False/None)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "skip": 0,
                "limit": 50,
                "search": "user@example",
                "verified_only": True
            }
        }
    )


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class AdminUserResponse(BaseModel):
    """
    Response schema for user data in admin operations.
    
    Represents a user object returned by admin endpoints. Never includes
    the hashed_password field for security.
    
    Attributes:
        id: Unique user identifier
        email: User's email address
        is_verified: Whether the user's email has been verified
        is_admin: Whether the user has admin privileges
        created_at: Timestamp when the user account was created
        updated_at: Timestamp when the user account was last updated
    """
    id: int
    email: str
    is_verified: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "is_verified": True,
                "is_admin": False,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )


class UserListResponse(BaseModel):
    """
    Response schema for paginated user list.
    
    Contains a list of users with pagination metadata.
    
    Attributes:
        users: List of user objects
        total: Total count of users matching the filters
        skip: Number of records skipped (pagination offset)
        limit: Maximum number of records returned per page
    """
    users: list[AdminUserResponse]
    total: int = Field(
        description="Total count of users matching the filters"
    )
    skip: int = Field(
        description="Number of records skipped (pagination offset)"
    )
    limit: int = Field(
        description="Maximum number of records returned per page"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "users": [
                    {
                        "id": 1,
                        "email": "user1@example.com",
                        "is_verified": True,
                        "is_admin": False,
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T10:30:00"
                    },
                    {
                        "id": 2,
                        "email": "user2@example.com",
                        "is_verified": False,
                        "is_admin": False,
                        "created_at": "2024-01-14T15:45:00",
                        "updated_at": "2024-01-14T15:45:00"
                    }
                ],
                "total": 100,
                "skip": 0,
                "limit": 50
            }
        }
    )


class AdminActionResponse(BaseModel):
    """
    Response schema for admin action results.
    
    Used for responses to create, update, delete, and verification toggle
    operations. Includes a message describing the result and optionally
    the affected user object.
    
    Attributes:
        message: Localized message describing the operation result
        user: Optional user data (included for create/update/verify operations)
    """
    message: str = Field(
        description="Localized message describing the operation result"
    )
    user: Optional[AdminUserResponse] = Field(
        default=None,
        description="User data (included for create/update/verify operations)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "User created successfully",
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "is_verified": True,
                    "is_admin": False,
                    "created_at": "2024-01-15T10:30:00",
                    "updated_at": "2024-01-15T10:30:00"
                }
            }
        }
    )
