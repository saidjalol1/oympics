"""
User response schemas.

This module defines Pydantic models for user-related API responses.
The schemas ensure that sensitive data like hashed passwords are never
exposed in API responses.
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime


class UserResponse(BaseModel):
    """
    Response schema for user data.
    
    This schema is used to return user information in API responses.
    It explicitly excludes the hashed_password field for security,
    ensuring that password hashes are never exposed to clients.
    
    Attributes:
        id: Unique user identifier
        email: User's email address
        is_verified: Whether the user's email has been verified
        created_at: Timestamp when the user account was created
    """
    id: int
    email: str
    is_verified: bool
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "is_verified": True,
                "created_at": "2024-01-15T10:30:00"
            }
        }
    )
