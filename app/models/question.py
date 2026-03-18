"""Question database model.

This module defines the Question SQLAlchemy model for individual assessment items.
"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Question(Base):
    """Question model for individual assessment items.
    
    Represents a single question within a Test with multiple choice options.
    Questions contain multiple QuestionOptions and can have up to 2 image attachments.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        test_id: Foreign key to Test, indexed for fast lookups
        text_en: Question text in English (1-1000 characters), indexed for fast lookups
        text_uz: Question text in Uzbek (1-1000 characters), indexed for fast lookups
        text_ru: Question text in Russian (1-1000 characters), indexed for fast lookups
        text: Legacy question text field (deprecated, kept for backward compatibility)
        correct_answer: Correct answer label (A-J)
        created_at: Timestamp when question was created
        updated_at: Timestamp when question was last updated
        test: Many-to-one relationship with Test model
        options: One-to-many relationship with QuestionOption model (cascade delete)
        images: One-to-many relationship with QuestionImage model (cascade delete)
    """
    
    __tablename__ = "questions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Multi-language fields
    text_en: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    text_uz: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    text_ru: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    
    # Legacy field (deprecated, kept for backward compatibility)
    text: Mapped[str | None] = mapped_column(String(1000), nullable=True, index=True)
    
    correct_answer: Mapped[str] = mapped_column(String(1), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    test: Mapped["Test"] = relationship(
        "Test",
        back_populates="questions",
        lazy="select"
    )
    options: Mapped[list["QuestionOption"]] = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="select"
    )
    images: Mapped[list["QuestionImage"]] = relationship(
        "QuestionImage",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("correct_answer IN ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J')", name="ck_question_correct_answer"),
        Index("idx_question_test_id", "test_id"),
        Index("idx_question_text_en", "text_en"),
        Index("idx_question_text", "text"),
    )
    
    def __repr__(self) -> str:
        """String representation of Question."""
        try:
            # Use object.__getattribute__ to avoid SQLAlchemy attribute access
            id_val = object.__getattribute__(self, '__dict__').get('id', 'Unknown')
            test_id_val = object.__getattribute__(self, '__dict__').get('test_id', 'Unknown')
            correct_answer_val = object.__getattribute__(self, '__dict__').get('correct_answer', 'Unknown')
            return f"<Question(id={id_val}, test_id={test_id_val}, correct_answer={correct_answer_val})>"
        except:
            return f"<Question at {hex(id(self))}>"


# Import Test, QuestionOption, and QuestionImage here to avoid circular imports
from app.models.test import Test  # noqa: E402, F401
from app.models.question_option import QuestionOption  # noqa: E402, F401
from app.models.question_image import QuestionImage  # noqa: E402, F401
