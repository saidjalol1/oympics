"""Test database model.

This module defines the Test SQLAlchemy model for organizing questions into assessments.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, DateTime, Integer, ForeignKey, Index, UniqueConstraint, CheckConstraint, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Test(Base):
    """Test model for organizing questions into assessments.
    
    Represents a collection of questions organized within a Level, with defined availability dates and pricing.
    Tests contain multiple Questions.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        level_id: Foreign key to Level, indexed for fast lookups
        name_en: Test name in English (1-100 characters), indexed for fast lookups
        name_uz: Test name in Uzbek (1-100 characters), indexed for fast lookups
        name_ru: Test name in Russian (1-100 characters), indexed for fast lookups
        name: Legacy test name field (deprecated, kept for backward compatibility)
        price: Test price as decimal (10 digits, 2 decimal places), must be >= 0
        start_date: Optional start date for test availability
        end_date: Optional end date for test availability
        created_at: Timestamp when test was created
        updated_at: Timestamp when test was last updated
        level: Many-to-one relationship with Level model
        questions: One-to-many relationship with Question model (cascade delete)
    """
    
    __tablename__ = "tests"
    __test__ = False  # Tell pytest this is not a test class
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level_id: Mapped[int] = mapped_column(Integer, ForeignKey("levels.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Multi-language fields
    name_en: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name_uz: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name_ru: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Legacy field (deprecated, kept for backward compatibility)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    
    # Pricing field
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False, default=Decimal("0.00"), index=True)
    
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    level: Mapped["Level"] = relationship(
        "Level",
        back_populates="tests",
        lazy="select"
    )
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="test",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("level_id", "name_en", name="uq_test_level_name_en"),
        CheckConstraint("end_date IS NULL OR start_date IS NULL OR end_date >= start_date", name="ck_test_date_range"),
        CheckConstraint("price >= 0", name="ck_test_price_non_negative"),
        Index("idx_test_level_id", "level_id"),
        Index("idx_test_name_en", "name_en"),
        Index("idx_test_name_uz", "name_uz"),
        Index("idx_test_name_ru", "name_ru"),
        Index("idx_test_price", "price"),
        Index("idx_test_dates", "start_date", "end_date"),
    )
    
    def __repr__(self) -> str:
        """String representation of Test."""
        return f"<Test(id={getattr(self, 'id', None)}, level_id={getattr(self, 'level_id', None)}, name_en={getattr(self, 'name_en', None)})>"


# Import Level and Question here to avoid circular imports
from app.models.level import Level  # noqa: E402, F401
from app.models.question import Question  # noqa: E402, F401
