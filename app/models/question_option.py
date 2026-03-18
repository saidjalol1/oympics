"""QuestionOption database model.

This module defines the QuestionOption SQLAlchemy model for answer choices.
"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class QuestionOption(Base):
    """QuestionOption model for answer choices.
    
    Represents a single answer choice for a Question, labeled A-J.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        question_id: Foreign key to Question, indexed for fast lookups
        label: Option label (A-J)
        text_en: Option text in English (1-1000 characters)
        text_uz: Option text in Uzbek (1-1000 characters)
        text_ru: Option text in Russian (1-1000 characters)
        text: Legacy option text field (deprecated, kept for backward compatibility)
        created_at: Timestamp when option was created
        updated_at: Timestamp when option was last updated
        question: Many-to-one relationship with Question model
    """
    
    __tablename__ = "question_options"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(1), nullable=False)
    
    # Multi-language fields
    text_en: Mapped[str] = mapped_column(String(1000), nullable=False)
    text_uz: Mapped[str] = mapped_column(String(1000), nullable=False)
    text_ru: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # Legacy field (deprecated, kept for backward compatibility)
    text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="options",
        lazy="select"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("question_id", "label", name="uq_question_option_label"),
        CheckConstraint("label IN ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J')", name="ck_question_option_label"),
        Index("idx_question_option_question_id", "question_id"),
        Index("idx_question_option_label", "label"),
        Index("idx_question_option_text_en", "text_en"),
        Index("idx_question_option_text_uz", "text_uz"),
        Index("idx_question_option_text_ru", "text_ru"),
    )
    
    def __repr__(self) -> str:
        """String representation of QuestionOption."""
        try:
            # Use object.__getattribute__ to avoid SQLAlchemy attribute access
            id_val = object.__getattribute__(self, '__dict__').get('id', 'Unknown')
            question_id_val = object.__getattribute__(self, '__dict__').get('question_id', 'Unknown')
            label_val = object.__getattribute__(self, '__dict__').get('label', 'Unknown')
            return f"<QuestionOption(id={id_val}, question_id={question_id_val}, label={label_val})>"
        except:
            return f"<QuestionOption at {hex(id(self))}>"


# Import Question here to avoid circular imports
from app.models.question import Question  # noqa: E402, F401
