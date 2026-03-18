"""Subject database model.

This module defines the Subject SQLAlchemy model for organizing tests by academic discipline.
"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Subject(Base):
    """Subject model for organizing tests by academic discipline.
    
    Represents a top-level category such as Mathematics, Biology, or Physics.
    Subjects contain multiple Levels, which in turn contain Tests and Questions.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        name_en: Subject name in English (1-100 characters), indexed for fast lookups
        name_uz: Subject name in Uzbek (1-100 characters), indexed for fast lookups
        name_ru: Subject name in Russian (1-100 characters), indexed for fast lookups
        name: Legacy subject name field (deprecated, kept for backward compatibility)
        created_at: Timestamp when subject was created
        updated_at: Timestamp when subject was last updated
        levels: One-to-many relationship with Level model (cascade delete)
    """
    
    __tablename__ = "subjects"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Multi-language fields
    name_en: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name_uz: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name_ru: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Legacy field (deprecated, kept for backward compatibility)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    levels: Mapped[list["Level"]] = relationship(
        "Level",
        back_populates="subject",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("name_en", name="uq_subject_name_en"),
        Index("idx_subject_name_en", "name_en"),
        Index("idx_subject_name_uz", "name_uz"),
        Index("idx_subject_name_ru", "name_ru"),
    )
    
    def __repr__(self) -> str:
        """String representation of Subject."""
        return f"<Subject(id={getattr(self, 'id', None)}, name_en={getattr(self, 'name_en', None)})>"


# Import Level here to avoid circular imports
from app.models.level import Level  # noqa: E402, F401
