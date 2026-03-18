"""Password hashing and verification service using bcrypt.

This module provides secure password hashing and verification functionality
using the bcrypt algorithm with a cost factor of 12.
"""

from passlib.context import CryptContext


class PasswordService:
    """Service for password hashing and verification.

    Uses bcrypt algorithm with cost factor 12 for secure password hashing.
    """

    BCRYPT_MAX_LENGTH = 72

    def __init__(self) -> None:
        """Initialize the password service with bcrypt context."""
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12
        )

    def hash_password(self, password: str) -> str:
        """Hash a plain text password using bcrypt.

        Args:
            password: The plain text password to hash (max 72 bytes)

        Returns:
            The hashed password string

        Raises:
            ValueError: If password exceeds 72 bytes
        """
        if len(password.encode('utf-8')) > self.BCRYPT_MAX_LENGTH:
            raise ValueError(f"Password cannot exceed {self.BCRYPT_MAX_LENGTH} bytes")
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain text password against a hashed password.

        Args:
            plain_password: The plain text password to verify (max 72 bytes)
            hashed_password: The hashed password to compare against

        Returns:
            True if the password matches, False otherwise

        Raises:
            ValueError: If password exceeds 72 bytes
        """
        if len(plain_password.encode('utf-8')) > self.BCRYPT_MAX_LENGTH:
            raise ValueError(f"Password cannot exceed {self.BCRYPT_MAX_LENGTH} bytes")
        return self.pwd_context.verify(plain_password, hashed_password)
