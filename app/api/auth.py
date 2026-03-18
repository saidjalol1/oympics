"""
Authentication API endpoints.

This module implements the authentication endpoints for user registration,
email verification, login, logout, and token refresh. All endpoints support
multi-language responses based on the Accept-Language header.
"""

import json
from typing import Annotated
from urllib.parse import urlparse

from fastapi import APIRouter, Cookie, Depends, Header, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_language
from app.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    ExpiredTokenError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.database import get_db
from app.i18n.translations import TranslationManager
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    AuthResponse,
    ErrorResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.password_service import PasswordService
from app.services.token_service import TokenService

# Initialize router and translation manager
router = APIRouter(prefix="/api/auth", tags=["authentication"])
translations = TranslationManager()


def is_safe_redirect_url(url: str, allowed_hosts: list[str] = None) -> bool:
    """Validate that redirect URL is safe (prevents open redirect attacks)."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        # Only allow relative URLs or URLs from allowed hosts
        if parsed.scheme and parsed.netloc:
            # Absolute URL - check if it's in allowed hosts
            if allowed_hosts and parsed.netloc not in allowed_hosts:
                return False
        return True
    except Exception:
        return False


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "User registered successfully. Verification email sent.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Registration successful. Please check your email to verify your account.",
                        "user": None
                    }
                }
            }
        },
        400: {
            "description": "Validation error (invalid email or short password)",
            "model": ErrorResponse,
        },
        409: {
            "description": "Email already registered",
            "model": ErrorResponse,
        },
        503: {
            "description": "Email service unavailable",
            "model": ErrorResponse,
        },
    },
)
async def register(
    request: RegisterRequest,
    language: Annotated[str, Depends(get_language)] = "en",
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Register a new user account.
    
    Creates a new user with the provided email and password. The user starts
    in an unverified state and receives a verification email. The password
    is hashed using bcrypt before storage.
    
    **Multi-language Support:**
    - English: "Registration successful. Please check your email to verify your account."
    - Russian: "Регистрация успешна. Пожалуйста, проверьте свою электронную почту для подтверждения учетной записи."
    - Uzbek: "Ro'yxatdan o'tish muvaffaqiyatli. Iltimos, hisobingizni tasdiqlash uchun elektron pochtangizni tekshiring."
    
    **Requirements:**
    - 1.1: Create pending user record
    - 1.2: Send verification email
    - 1.3: Reject duplicate email
    - 1.4: Validate email format
    - 1.5: Validate password length (min 8 chars)
    - 1.6: Hash password before storage
    - 1.7: User starts unverified
    - 7.1: Detect language from Accept-Language header
    - 7.7: Return localized success message
    """
    try:
        user_repo = UserRepository(db)
        password_service = PasswordService()
        token_service = TokenService()
        email_service = EmailService()
        auth_service = AuthService(user_repo, password_service, token_service, email_service)
        
        user, verification_token = await auth_service.register_user(
            request.email, request.password, language
        )
        
        message = translations.get("registration_success", language)
        return AuthResponse(message=message, user=None)
        
    except EmailAlreadyExistsError as e:
        message = translations.get("email_already_exists", language)
        raise EmailAlreadyExistsError(message)
    except Exception as e:
        # Validation errors from Pydantic are handled by FastAPI
        raise


@router.get(
    "/verify",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Email verified successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Email verified successfully. You are now logged in.",
                        "user": None
                    }
                }
            }
        },
        400: {
            "description": "Invalid verification token",
            "model": ErrorResponse,
        },
        401: {
            "description": "Verification token expired",
            "model": ErrorResponse,
        },
    },
)
async def verify_email(
    token: str,
    redirect_url: str | None = None,
    language: Annotated[str, Depends(get_language)] = "en",
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Verify user email address.
    
    Validates the verification token, marks the user as verified, creates
    session tokens (access and refresh), and returns a JSON response with
    the session cookie set. Optionally redirects to a specified URL if provided.
    
    **Parameters:**
    - token: Email verification token (required)
    - redirect_url: Optional URL to redirect to after verification (relative or absolute)
    
    **Examples:**
    - `/api/auth/verify?token=xxx` - Returns JSON response
    - `/api/auth/verify?token=xxx&redirect_url=/dashboard` - Redirects to /dashboard
    - `/api/auth/verify?token=xxx&redirect_url=https://yourfrontend.com/dashboard` - Redirects to frontend
    
    **Requirements:**
    - 2.1: Convert pending user to verified user
    - 2.2: Create access and refresh tokens
    - 2.3: Return JSON response with session cookie
    - 2.4: Reject invalid tokens
    - 2.5: Reject expired tokens
    - 2.6: Verification tokens expire in 24 hours
    - 15.1: Set HttpOnly flag on cookie
    - 15.3: Set SameSite=Lax on cookie
    - 15.4: Include both tokens in cookie
    - 15.5: Set Max-Age to 7 days
    """
    try:
        user_repo = UserRepository(db)
        password_service = PasswordService()
        token_service = TokenService()
        email_service = EmailService()
        auth_service = AuthService(user_repo, password_service, token_service, email_service)
        
        user, access_token, refresh_token = await auth_service.verify_email(token)
        
        # Create session cookie with both tokens
        session_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        
        # If redirect_url is provided and valid, redirect with cookie
        if redirect_url and is_safe_redirect_url(redirect_url):
            redirect_response = RedirectResponse(
                url=redirect_url,
                status_code=status.HTTP_302_FOUND
            )
            redirect_response.set_cookie(
                key=settings.cookie_name,
                value=json.dumps(session_data),
                httponly=settings.cookie_httponly,
                secure=settings.cookie_secure,
                samesite=settings.cookie_samesite,
                max_age=settings.cookie_max_age,
                path=settings.cookie_path,
            )
            return redirect_response
        
        # Otherwise, return JSON response
        response = AuthResponse(
            message=translations.get("verification_success", language),
            user=None
        )
        
        # Create a JSONResponse wrapper to set cookies
        json_response = JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response.model_dump()
        )
        json_response.set_cookie(
            key=settings.cookie_name,
            value=json.dumps(session_data),
            httponly=settings.cookie_httponly,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=settings.cookie_max_age,
            path=settings.cookie_path,
        )
        
        return json_response
        
    except InvalidTokenError:
        message = translations.get("invalid_token", language)
        raise AuthenticationError(message)
    except ExpiredTokenError:
        message = translations.get("token_expired", language)
        raise AuthenticationError(message)


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Login successful. Session cookie set.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Login successful",
                        "user": {
                            "id": 1,
                            "email": "user@example.com",
                            "is_verified": True,
                            "created_at": "2024-01-15T10:30:00"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Invalid credentials",
            "model": ErrorResponse,
        },
        403: {
            "description": "Email not verified",
            "model": ErrorResponse,
        },
    },
)
async def login(
    request: LoginRequest,
    response: Response,
    language: Annotated[str, Depends(get_language)] = "en",
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Authenticate user and create session.
    
    Validates email and password credentials, verifies the user's email
    is confirmed, creates session tokens, and sets the session cookie.
    
    **Multi-language Support:**
    - English: "Login successful"
    - Russian: "Вход выполнен успешно"
    - Uzbek: "Kirish muvaffaqiyatli"
    
    **Requirements:**
    - 3.1: Create access and refresh tokens for verified users
    - 3.2: Return localized success message
    - 3.3: Reject invalid credentials
    - 3.4: Reject unverified users
    - 3.5: Access token expires in 15 minutes
    - 3.6: Refresh token expires in 7 days
    - 7.1: Detect language from Accept-Language header
    - 15.1: Set HttpOnly flag on cookie
    - 15.3: Set SameSite=Lax on cookie
    - 15.4: Include both tokens in cookie
    - 15.5: Set Max-Age to 7 days
    """
    try:
        user_repo = UserRepository(db)
        password_service = PasswordService()
        token_service = TokenService()
        email_service = EmailService()
        auth_service = AuthService(user_repo, password_service, token_service, email_service)
        
        user, access_token, refresh_token = await auth_service.login(
            request.email, request.password
        )
        
        # Create session cookie with both tokens
        session_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        
        response.set_cookie(
            key=settings.cookie_name,
            value=json.dumps(session_data),
            httponly=settings.cookie_httponly,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=settings.cookie_max_age,
            path=settings.cookie_path,
        )
        
        message = translations.get("login_success", language)
        user_response = UserResponse.model_validate(user)
        return AuthResponse(message=message, user=user_response)
        
    except InvalidCredentialsError:
        message = translations.get("invalid_credentials", language)
        raise AuthenticationError(message)
    except EmailNotVerifiedError:
        message = translations.get("email_not_verified", language)
        raise AuthorizationError(message)


@router.post(
    "/logout",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Logout successful. Session cookie cleared.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Logout successful",
                        "user": None
                    }
                }
            }
        },
    },
)
async def logout(
    response: Response,
    language: Annotated[str, Depends(get_language)] = "en",
) -> AuthResponse:
    """
    End user session.
    
    Clears the session cookie on the client side. No authentication required.
    Since refresh tokens are stateless JWT tokens, they remain technically 
    valid until expiration, but the client no longer has access to them after logout.
    
    **Multi-language Support:**
    - English: "Logout successful"
    - Russian: "Выход выполнен успешно"
    - Uzbek: "Chiqish muvaffaqiyatli"
    
    **Requirements:**
    - 4.1: Clear session cookie
    - 4.2: Return localized success message
    - 7.1: Detect language from Accept-Language header
    """
    response.delete_cookie(
        key=settings.cookie_name,
        path=settings.cookie_path,
        secure=settings.cookie_secure,
        httponly=settings.cookie_httponly,
        samesite=settings.cookie_samesite,
    )
    
    message = translations.get("logout_success", language)
    return AuthResponse(message=message, user=None)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Token refresh successful. Session cookie updated.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Token refreshed successfully",
                        "user": None
                    }
                }
            }
        },
        401: {
            "description": "Invalid or expired refresh token",
            "model": ErrorResponse,
        },
    },
)
async def refresh_token(
    response: Response,
    language: Annotated[str, Depends(get_language)] = "en",
    session: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Refresh access token.
    
    Validates the refresh token, generates a new access token with fresh
    expiration, and updates the session cookie. The refresh token itself
    remains unchanged.
    
    **Requirements:**
    - 5.1: Verify refresh token and generate new access token
    - 5.2: Update session cookie with new access token
    - 5.3: Reject invalid refresh tokens
    - 5.4: Reject expired refresh tokens
    - 5.5: Maintain same refresh token
    - 7.1: Detect language from Accept-Language header
    - 15.1: Set HttpOnly flag on cookie
    - 15.3: Set SameSite=Lax on cookie
    - 15.4: Include both tokens in cookie
    - 15.5: Set Max-Age to 7 days
    """
    try:
        # Extract refresh token from session cookie
        if not session:
            message = translations.get("not_authenticated", language)
            raise AuthenticationError(message)
        
        try:
            session_data = json.loads(session)
            refresh_token_str = session_data.get("refresh_token")
            
            if not refresh_token_str:
                message = translations.get("invalid_session", language)
                raise AuthenticationError(message)
        except json.JSONDecodeError:
            message = translations.get("invalid_session", language)
            raise AuthenticationError(message)
        
        # Generate new access token
        user_repo = UserRepository(db)
        password_service = PasswordService()
        token_service = TokenService()
        email_service = EmailService()
        auth_service = AuthService(user_repo, password_service, token_service, email_service)
        
        new_access_token = await auth_service.refresh_access_token(refresh_token_str)
        
        # Update session cookie with new access token
        new_session_data = {
            "access_token": new_access_token,
            "refresh_token": refresh_token_str,
        }
        
        response.set_cookie(
            key=settings.cookie_name,
            value=json.dumps(new_session_data),
            httponly=settings.cookie_httponly,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=settings.cookie_max_age,
            path=settings.cookie_path,
        )
        
        message = translations.get("token_refreshed", language)
        return AuthResponse(message=message, user=None)
        
    except (InvalidTokenError, ExpiredTokenError) as e:
        message = translations.get("invalid_token", language)
        raise AuthenticationError(message)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Current user information",
        },
        401: {
            "description": "Not authenticated",
        },
    },
)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)] = None,
) -> UserResponse:
    """
    Get current authenticated user information.
    
    Returns the current user's details including email, verification status, and admin status.
    
    **Requirements:**
    - User must be authenticated
    - Returns user email, is_verified, is_admin, and created_at
    """
    return UserResponse.model_validate(current_user)
