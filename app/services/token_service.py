"""
Token service for JWT token operations.

This module handles creation and validation of JWT tokens for authentication,
including access tokens, refresh tokens, and email verification tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict

from jose import JWTError, jwt

from app.config import settings


class TokenService:
    """
    Service for JWT token creation and validation.
    
    Handles three types of tokens:
    - Access tokens: Short-lived tokens for API authentication (15 minutes)
    - Refresh tokens: Long-lived tokens for obtaining new access tokens (7 days)
    - Verification tokens: Tokens for email verification (24 hours)
    
    Each token includes a 'type' field in the payload to prevent token confusion attacks.
    """
    
    def __init__(self) -> None:
        """Initialize the token service with configuration from settings."""
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
    
    def create_access_token(
        self, 
        user_id: int, 
        expires_delta: timedelta | None = None
    ) -> str:
        """
        Create a JWT access token for API authentication.
        
        Access tokens are short-lived (default 15 minutes) and used to authenticate
        API requests. They should be included in HTTP-only cookies.
        
        Args:
            user_id: The ID of the user for whom to create the token
            expires_delta: Optional custom expiration time. If not provided,
                          uses the configured default (15 minutes)
        
        Returns:
            A signed JWT token string
        
        Example:
            >>> token_service = TokenService()
            >>> token = token_service.create_access_token(user_id=123)
            >>> # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        
        expire = datetime.now(timezone.utc) + expires_delta
        
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        
        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(
        self, 
        user_id: int, 
        expires_delta: timedelta | None = None
    ) -> str:
        """
        Create a JWT refresh token for obtaining new access tokens.
        
        Refresh tokens are long-lived (default 7 days) and used to obtain new
        access tokens without requiring the user to log in again. They are
        stateless and not stored in the database.
        
        Args:
            user_id: The ID of the user for whom to create the token
            expires_delta: Optional custom expiration time. If not provided,
                          uses the configured default (7 days)
        
        Returns:
            A signed JWT token string
        
        Example:
            >>> token_service = TokenService()
            >>> token = token_service.create_refresh_token(user_id=123)
            >>> # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        """
        if expires_delta is None:
            expires_delta = timedelta(days=settings.refresh_token_expire_days)
        
        expire = datetime.now(timezone.utc) + expires_delta
        
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        
        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_verification_token(
        self, 
        user_id: int, 
        expires_delta: timedelta | None = None
    ) -> str:
        """
        Create a JWT token for email verification.
        
        Verification tokens are used in email verification links and expire
        after 24 hours by default. Once used to verify an email, the user's
        is_verified status is updated.
        
        Args:
            user_id: The ID of the user for whom to create the token
            expires_delta: Optional custom expiration time. If not provided,
                          uses the configured default (24 hours)
        
        Returns:
            A signed JWT token string
        
        Example:
            >>> token_service = TokenService()
            >>> token = token_service.create_verification_token(user_id=123)
            >>> # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=settings.verification_token_expire_hours)
        
        expire = datetime.now(timezone.utc) + expires_delta
        
        payload = {
            "sub": str(user_id),
            "type": "verification",
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        
        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Dict[str, any]:
        """
        Decode and validate a JWT token.
        
        This method verifies the token signature, checks expiration, and returns
        the payload. It raises exceptions for invalid or expired tokens.
        
        Args:
            token: The JWT token string to decode
        
        Returns:
            A dictionary containing the token payload with keys:
            - sub: User ID (as string)
            - type: Token type ("access", "refresh", or "verification")
            - exp: Expiration timestamp
            - iat: Issued at timestamp
        
        Raises:
            InvalidTokenError: If the token is malformed or has an invalid signature
            ExpiredTokenError: If the token has expired
        
        Example:
            >>> token_service = TokenService()
            >>> payload = token_service.decode_token(token)
            >>> # Returns: {"sub": "123", "type": "access", "exp": 1234567890, ...}
        """
        from app.core.exceptions import InvalidTokenError, ExpiredTokenError
        
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ExpiredTokenError("Token has expired")
        except JWTError:
            raise InvalidTokenError("Invalid token")
