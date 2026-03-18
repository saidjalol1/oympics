"""QuestionImage database model.

This module defines the QuestionImage SQLAlchemy model for image attachments to questions.
"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class QuestionImage(Base):
    """QuestionImage model for storing image attachments to questions.
    
    Represents an image file attached to a question. Each question can have up to 2 images.
    Images are stored in the file system with metadata in the database.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        question_id: Foreign key to Question, indexed for fast lookups
        image_path: Relative path to image file in uploads directory (max 500 characters)
        image_order: Order of image (1 or 2)
        original_filename: Original filename when uploaded (max 255 characters)
        file_size: File size in bytes (must be > 0 and <= 5242880 bytes = 5MB)
        width: Image width in pixels (must be >= 100 and <= 4000)
        height: Image height in pixels (must be >= 100 and <= 4000)
        created_at: Timestamp when image was uploaded
        question: Many-to-one relationship with Question model
    """
    
    __tablename__ = "question_images"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    image_order: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="images",
        lazy="select"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("question_id", "image_order", name="uq_question_image_order"),
        CheckConstraint("image_order IN (1, 2)", name="ck_question_image_order"),
        CheckConstraint("file_size > 0 AND file_size <= 5242880", name="ck_question_image_file_size"),
        CheckConstraint("width >= 100 AND width <= 4000", name="ck_question_image_width"),
        CheckConstraint("height >= 100 AND height <= 4000", name="ck_question_image_height"),
        Index("idx_question_image_question_id", "question_id"),
    )
    
    def __repr__(self) -> str:
        """String representation of QuestionImage."""
        try:
            # Use object.__getattribute__ to avoid SQLAlchemy attribute access
            id_val = object.__getattribute__(self, '__dict__').get('id', 'Unknown')
            question_id_val = object.__getattribute__(self, '__dict__').get('question_id', 'Unknown')
            image_order_val = object.__getattribute__(self, '__dict__').get('image_order', 'Unknown')
            return f"<QuestionImage(id={id_val}, question_id={question_id_val}, order={image_order_val})>"
        except:
            return f"<QuestionImage at {hex(id(self))}>"


# Import Question here to avoid circular imports
from app.models.question import Question  # noqa: E402, F401
