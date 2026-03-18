"""User database model.

This module defines the User SQLAlchemy model for storing user authentication data.
"""

from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class User(Base):
    """User model for authentication.
    
    Stores user credentials, verification status, and admin role for the authentication system.
    Passwords are stored as bcrypt hashes, never in plain text.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        email: Unique email address, indexed for fast lookups
        hashed_password: Bcrypt hash of user's password
        is_verified: Whether user has verified their email address
        is_admin: Whether user has admin privileges for admin panel access
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
    """
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email}, is_admin={self.is_admin})>"


# Create composite index for common query patterns
__table_args__ = (
    Index('idx_users_email', 'email'),
    Index('idx_users_verified', 'is_verified'),
    Index('idx_users_admin', 'is_admin'),
    Index('idx_users_verified_created', 'is_verified', 'created_at'),
)
