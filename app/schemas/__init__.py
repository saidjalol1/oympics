"""Pydantic schemas for request/response validation."""

from app.schemas.admin import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    UserListQueryParams,
    AdminUserResponse,
    UserListResponse,
    AdminActionResponse,
)
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    VerifyEmailRequest,
    AuthResponse,
    ErrorResponse,
)
from app.schemas.user import (
    UserResponse,
)
from app.schemas.test_management import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    SubjectListResponse,
    LevelCreate,
    LevelUpdate,
    LevelResponse,
    LevelListResponse,
    TestCreate,
    TestUpdate,
    TestResponse,
    TestListResponse,
    OptionInput,
    OptionResponse,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionListResponse,
    ErrorResponse,
)

__all__ = [
    # Admin schemas
    "AdminCreateUserRequest",
    "AdminUpdateUserRequest",
    "UserListQueryParams",
    "AdminUserResponse",
    "UserListResponse",
    "AdminActionResponse",
    # Auth schemas
    "LoginRequest",
    "RegisterRequest",
    "VerifyEmailRequest",
    "AuthResponse",
    "ErrorResponse",
    # User schemas
    "UserResponse",
    # Test management schemas
    "SubjectCreate",
    "SubjectUpdate",
    "SubjectResponse",
    "SubjectListResponse",
    "LevelCreate",
    "LevelUpdate",
    "LevelResponse",
    "LevelListResponse",
    "TestCreate",
    "TestUpdate",
    "TestResponse",
    "TestListResponse",
    "OptionInput",
    "OptionResponse",
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionResponse",
    "QuestionListResponse",
    "ErrorResponse",
]
