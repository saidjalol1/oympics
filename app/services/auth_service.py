"""
Authentication service for business logic orchestration.

This module provides the AuthService class that orchestrates all authentication
operations including registration, email verification, login, logout, and token refresh.
It coordinates between repositories and utility services to implement business rules.
"""

from typing import Tuple

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.password_service import PasswordService
from app.services.token_service import TokenService
from app.services.email_service import EmailService
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    EmailNotVerifiedError,
    InvalidTokenError,
    ExpiredTokenError,
)


class AuthService:
    """
    Service for authentication business logic.
    
    Orchestrates operations between UserRepository, PasswordService, TokenService,
    and EmailService to implement authentication workflows. Validates business rules
    and handles error conditions.
    
    Requirements:
        - 12.1: Service implements all authentication business logic
        - 12.2: Service orchestrates operations between Repository and utility services
        - 12.3: Service validates business rules before calling Repository methods
        - 12.5: Service returns structured responses for endpoints
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        password_service: PasswordService,
        token_service: TokenService,
        email_service: EmailService,
    ) -> None:
        """
        Initialize the authentication service with dependencies.
        
        Args:
            user_repository: Repository for user data access
            password_service: Service for password hashing and verification
            token_service: Service for JWT token operations
            email_service: Service for sending emails
        """
        self.user_repo = user_repository
        self.password_service = password_service
        self.token_service = token_service
        self.email_service = email_service
    
    async def register_user(
        self,
        email: str,
        password: str,
        language: str = "en"
    ) -> Tuple[User, str]:
        """
        Register a new user and send verification email.
        
        Creates a pending user account (is_verified=False), generates a verification
        token, and sends a verification email to the user. The user must verify their
        email before they can log in.
        
        Args:
            email: User's email address
            password: User's plain text password (will be hashed)
            language: Language code for email content ("en", "ru", or "uz")
        
        Returns:
            A tuple of (User, verification_token)
        
        Raises:
            EmailAlreadyExistsError: If email is already registered
            EmailSendError: If verification email fails to send
        
        Requirements:
            - 1.1: Create Pending_User record with valid email and password
            - 1.2: Send verification email to provided address
            - 1.3: Return error if email already exists
            - 1.6: Hash all passwords before storage
            - 1.7: Do not create Verified_User until email verification
        
        Example:
            >>> auth_service = AuthService(...)
            >>> user, token = await auth_service.register_user(
            ...     email="user@example.com",
            ...     password="securepass123",
            ...     language="en"
            ... )
            >>> user.is_verified
            False
        """
        # Check if email already exists
        if await self.user_repo.exists_by_email(email):
            raise EmailAlreadyExistsError("email_already_exists")
        
        # Hash the password
        hashed_password = self.password_service.hash_password(password)
        
        # Create pending user (is_verified=False)
        user = await self.user_repo.create(
            email=email,
            hashed_password=hashed_password,
            is_verified=False
        )
        
        # Generate verification token
        verification_token = self.token_service.create_verification_token(user.id)
        
        # Send verification email
        await self.email_service.send_verification_email(
            email=email,
            verification_token=verification_token,
            language=language
        )
        
        return user, verification_token
    
    async def verify_email(self, token: str) -> Tuple[User, str, str]:
        """
        Verify user email and create session tokens.
        
        Validates the verification token, updates the user's verification status,
        and generates access and refresh tokens for immediate login.
        
        Args:
            token: JWT verification token from email link
        
        Returns:
            A tuple of (User, access_token, refresh_token)
        
        Raises:
            InvalidTokenError: If token is malformed or has invalid signature
            ExpiredTokenError: If token has expired
            ResourceNotFoundError: If user associated with token doesn't exist
        
        Requirements:
            - 2.1: Convert Pending_User to Verified_User
            - 2.2: Create Session_Cookie with Access_Token and Refresh_Token
            - 2.4: Return error for invalid verification token
            - 2.5: Return error for expired verification token
        
        Example:
            >>> auth_service = AuthService(...)
            >>> user, access_token, refresh_token = await auth_service.verify_email(token)
            >>> user.is_verified
            True
        """
        # Decode and validate token
        try:
            payload = self.token_service.decode_token(token)
        except ExpiredTokenError:
            raise ExpiredTokenError("expired_token")
        except InvalidTokenError:
            raise InvalidTokenError("invalid_token")
        
        # Verify token type
        if payload.get("type") != "verification":
            raise InvalidTokenError("invalid_token")
        
        # Get user ID from token
        user_id = int(payload.get("sub"))
        
        # Get user from database
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError("invalid_token")
        
        # Update verification status
        user = await self.user_repo.update_verification_status(user_id, True)
        
        # Generate session tokens
        access_token = self.token_service.create_access_token(user.id)
        refresh_token = self.token_service.create_refresh_token(user.id)
        
        return user, access_token, refresh_token
    
    async def login(
        self,
        email: str,
        password: str
    ) -> Tuple[User, str, str]:
        """
        Authenticate user and create session tokens.
        
        Validates user credentials, checks verification status, and generates
        access and refresh tokens for the session.
        
        Args:
            email: User's email address
            password: User's plain text password
        
        Returns:
            A tuple of (User, access_token, refresh_token)
        
        Raises:
            InvalidCredentialsError: If email or password is incorrect
            EmailNotVerifiedError: If user hasn't verified their email
        
        Requirements:
            - 3.1: Create Session_Cookie with tokens for valid credentials
            - 3.3: Return error for invalid credentials
            - 3.4: Return error for Pending_User (unverified email)
        
        Example:
            >>> auth_service = AuthService(...)
            >>> user, access_token, refresh_token = await auth_service.login(
            ...     email="user@example.com",
            ...     password="securepass123"
            ... )
        """
        # Get user by email
        user = await self.user_repo.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError("invalid_credentials")
        
        # Verify password
        if not self.password_service.verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("invalid_credentials")
        
        # Check if email is verified
        if not user.is_verified:
            raise EmailNotVerifiedError("email_not_verified")
        
        # Generate session tokens
        access_token = self.token_service.create_access_token(user.id)
        refresh_token = self.token_service.create_refresh_token(user.id)
        
        return user, access_token, refresh_token
    
    async def logout(self) -> None:
        """
        End user session (client clears cookies).
        
        With stateless JWT tokens, logout is handled entirely client-side by
        clearing the session cookie. No database operations are needed.
        
        Note: Since refresh tokens are stateless and not stored in the database,
        they remain technically valid until expiration. This is a trade-off for
        the stateless architecture - true token revocation would require database
        storage or a token blacklist.
        
        Requirements:
            - 4.1: Clear Session_Cookie on logout request
        
        Example:
            >>> auth_service = AuthService(...)
            >>> await auth_service.logout()
        """
        # No database operations needed for stateless tokens
        # Cookie clearing is handled by the API endpoint
        pass
    
    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate new access token from valid refresh token.
        
        Validates the refresh token and generates a new access token with a
        fresh expiration time. The refresh token itself remains unchanged.
        
        Args:
            refresh_token: JWT refresh token from session cookie
        
        Returns:
            A new access token string
        
        Raises:
            InvalidTokenError: If token is malformed or has invalid signature
            ExpiredTokenError: If refresh token has expired
        
        Requirements:
            - 5.1: Verify JWT signature and expiration
            - 5.2: Generate new Access_Token
            - 5.4: Return error for invalid JWT signature
            - 5.5: Return error for expired Refresh_Token
            - 5.6: Maintain same Refresh_Token when generating new Access_Token
        
        Example:
            >>> auth_service = AuthService(...)
            >>> new_access_token = await auth_service.refresh_access_token(refresh_token)
        """
        # Decode and validate token
        try:
            payload = self.token_service.decode_token(refresh_token)
        except ExpiredTokenError:
            raise ExpiredTokenError("expired_token")
        except InvalidTokenError:
            raise InvalidTokenError("invalid_token")
        
        # Verify token type
        if payload.get("type") != "refresh":
            raise InvalidTokenError("invalid_token")
        
        # Get user ID from token
        user_id = int(payload.get("sub"))
        
        # Generate new access token
        new_access_token = self.token_service.create_access_token(user_id)
        
        return new_access_token
