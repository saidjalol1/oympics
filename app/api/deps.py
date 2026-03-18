"""
API dependencies for FastAPI endpoints.

This module provides dependency injection functions for FastAPI routes,
including user authentication and language detection.
"""

import json
from typing import Annotated

from fastapi import Cookie, Depends, Header, Request

from app.core.exceptions import AuthenticationError, InvalidTokenError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.token_service import TokenService
from app.database import get_db
from app.i18n.language import detect_language
from sqlalchemy.ext.asyncio import AsyncSession


async def get_current_user(
    request: Request,
    session: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency for extracting and validating access token from cookie.
    
    This dependency extracts the session cookie, validates the access token,
    and returns the authenticated user. It should be used on protected endpoints
    that require authentication.
    
    The session cookie contains a JSON object with access_token and refresh_token.
    This function validates the access token and retrieves the user from the database.
    
    Args:
        request: The FastAPI request object
        session: The session cookie value containing tokens (optional)
        db: Database session from dependency injection
    
    Returns:
        The authenticated User object
    
    Raises:
        AuthenticationError: If the session cookie is missing, invalid, or expired
    
    Example:
        ```python
        @router.get("/protected")
        async def protected_route(
            current_user: User = Depends(get_current_user)
        ):
            return {"user_id": current_user.id}
        ```
    
    Requirements:
        - 7.1: Extract authentication information from request
    """
    # Check if session cookie exists
    if not session:
        raise AuthenticationError("Not authenticated")
    
    try:
        # Parse the session cookie JSON
        session_data = json.loads(session)
        access_token = session_data.get("access_token")
        
        if not access_token:
            raise AuthenticationError("Invalid session")
        
        # Validate the access token
        token_service = TokenService()
        payload = token_service.decode_token(access_token)
        
        # Verify token type
        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")
        
        # Extract user ID from token
        user_id = int(payload.get("sub"))
        
        # Retrieve user from database
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            raise AuthenticationError("User not found")
        
        return user
        
    except json.JSONDecodeError:
        raise AuthenticationError("Invalid session format")
    except (ValueError, KeyError):
        raise AuthenticationError("Invalid session data")
    except InvalidTokenError:
        raise AuthenticationError("Invalid or expired token")


def get_language(
    accept_language: Annotated[str | None, Header()] = None
) -> str:
    """
    Dependency for detecting user language from Accept-Language header.
    
    This dependency extracts the Accept-Language header from the request
    and returns the detected language code. It supports English (en),
    Russian (ru), and Uzbek (uz), defaulting to English if the header
    is missing or contains unsupported languages.
    
    Args:
        accept_language: The Accept-Language header value (optional)
    
    Returns:
        A supported language code: "en", "ru", or "uz"
    
    Example:
        ```python
        @router.post("/register")
        async def register(
            data: RegisterRequest,
            language: str = Depends(get_language)
        ):
            # Use language for localized responses
            return {"message": translations.get("success", language)}
        ```
    
    Requirements:
        - 7.1: Detect user language from Accept-Language header
    """
    return detect_language(accept_language)


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency for verifying admin role on protected endpoints.
    
    This dependency verifies that the current authenticated user has admin privileges
    by checking the is_admin flag from the database. It uses the existing get_current_user
    dependency to ensure the user is authenticated, then performs an additional
    authorization check for admin role.
    
    The admin status is verified from the current database state (not from a cached
    token), ensuring that admin privileges are always current and can be revoked
    immediately by updating the database.
    
    Args:
        current_user: Authenticated user from get_current_user dependency
        db: Database session from dependency injection
    
    Returns:
        The authenticated User object if admin check passes
    
    Raises:
        AuthorizationError: If user is not an admin (is_admin != True)
    
    Example:
        ```python
        @router.get("/api/admin/users")
        async def list_users(
            current_admin: User = Depends(get_current_admin_user)
        ):
            return {"admin_id": current_admin.id}
        ```
    
    Preconditions:
        - current_user must be authenticated (valid session cookie)
        - current_user must exist in database
        - Database connection must be active
    
    Postconditions:
        - Returns current_user if is_admin == True
        - Raises AuthorizationError if is_admin == False
        - Does not modify user state or session
    
    Requirements:
        - 9.1: Non-admin users cannot access admin endpoints
        - 9.2: Unauthenticated users cannot access admin endpoints
        - 9.3: Admin status verified from database (not token)
        - 9.4: Authorization error message "Admin access required"
        - 9.5: Proceed with operation if authorization succeeds
        - 21.1: Admin status verified from database
    """
    from app.core.exceptions import AuthorizationError
    
    # Verify user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin access required")
    
    return current_user
