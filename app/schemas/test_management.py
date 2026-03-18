"""Test management request and response schemas.

This module defines Pydantic models for test management API requests and responses,
including subjects, levels, tests, and questions with comprehensive validation.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime


# ============================================================================
# SUBJECT SCHEMAS
# ============================================================================

class SubjectCreate(BaseModel):
    """Request schema for creating a subject."""
    # Multi-language fields
    name_en: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Subject name in English (1-100 characters)"
    )
    name_uz: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Subject name in Uzbek (1-100 characters)"
    )
    name_ru: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Subject name in Russian (1-100 characters)"
    )
    
    # Legacy field (deprecated, kept for backward compatibility)
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Subject name (legacy field, use name_en/name_uz/name_ru instead)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name_en": "Mathematics",
                "name_uz": "Matematika",
                "name_ru": "Математика"
            }
        }
    )


class SubjectUpdate(BaseModel):
    """Request schema for updating a subject."""
    # Multi-language fields
    name_en: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Subject name in English (1-100 characters)"
    )
    name_uz: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Subject name in Uzbek (1-100 characters)"
    )
    name_ru: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Subject name in Russian (1-100 characters)"
    )
    
    # Legacy field (deprecated, kept for backward compatibility)
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Subject name (legacy field, use name_en/name_uz/name_ru instead)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name_en": "Advanced Mathematics",
                "name_uz": "Ilg'or matematika",
                "name_ru": "Продвинутая математика"
            }
        }
    )


class SubjectResponse(BaseModel):
    """Response schema for subject data."""
    id: int
    name_en: str
    name_uz: str
    name_ru: str
    name: Optional[str] = None  # Legacy field for backward compatibility
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name_en": "Mathematics",
                "name_uz": "Matematika",
                "name_ru": "Математика",
                "name": "Mathematics",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )


# ============================================================================
# LEVEL SCHEMAS
# ============================================================================

class LevelCreate(BaseModel):
    """Request schema for creating a level."""
    # Multi-language fields
    name_en: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Level name in English (1-100 characters)"
    )
    name_uz: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Level name in Uzbek (1-100 characters)"
    )
    name_ru: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Level name in Russian (1-100 characters)"
    )
    
    # Legacy field (deprecated, kept for backward compatibility)
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Level name (legacy field, use name_en/name_uz/name_ru instead)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name_en": "Grade 5",
                "name_uz": "5-sinf",
                "name_ru": "5 класс"
            }
        }
    )


class LevelUpdate(BaseModel):
    """Request schema for updating a level."""
    # Multi-language fields
    name_en: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Level name in English (1-100 characters)"
    )
    name_uz: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Level name in Uzbek (1-100 characters)"
    )
    name_ru: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Level name in Russian (1-100 characters)"
    )
    
    # Legacy field (deprecated, kept for backward compatibility)
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Level name (legacy field, use name_en/name_uz/name_ru instead)"
    )
    
    # Subject ID (optional for updates)
    subject_id: Optional[int] = Field(
        default=None,
        description="Subject ID to move level to (optional)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name_en": "Grade 6",
                "name_uz": "6-sinf",
                "name_ru": "6 класс",
                "subject_id": 1
            }
        }
    )


class LevelResponse(BaseModel):
    """Response schema for level data."""
    id: int
    subject_id: int
    name_en: str
    name_uz: str
    name_ru: str
    name: Optional[str] = None  # Legacy field for backward compatibility
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "subject_id": 1,
                "name_en": "Grade 5",
                "name_uz": "5-sinf",
                "name_ru": "5 класс",
                "name": "Grade 5",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )


# ============================================================================
# NESTED RESPONSE SCHEMAS (for relationships)
# ============================================================================

class LevelWithSubjectResponse(BaseModel):
    """Response schema for level data with nested subject."""
    id: int
    subject_id: int
    name_en: str
    name_uz: str
    name_ru: str
    name: Optional[str] = None  # Legacy field for backward compatibility
    subject: SubjectResponse  # Nested subject data
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "subject_id": 1,
                "name_en": "Grade 5",
                "name_uz": "5-sinf",
                "name_ru": "5 класс",
                "name": "Grade 5",
                "subject": {
                    "id": 1,
                    "name_en": "Mathematics",
                    "name_uz": "Matematika",
                    "name_ru": "Математика",
                    "name": "Mathematics",
                    "created_at": "2024-01-15T10:30:00",
                    "updated_at": "2024-01-15T10:30:00"
                },
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )


# ============================================================================
# TEST SCHEMAS
# ============================================================================

class TestCreate(BaseModel):
    """Request schema for creating a test."""
    # Multi-language fields
    name_en: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Test name in English (1-100 characters)"
    )
    name_uz: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Test name in Uzbek (1-100 characters)"
    )
    name_ru: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Test name in Russian (1-100 characters)"
    )
    
    # Legacy field (deprecated, kept for backward compatibility)
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Test name (legacy field, use name_en/name_uz/name_ru instead)"
    )
    
    # Level ID (required for global endpoint)
    level_id: int = Field(
        description="Parent level ID"
    )
    
    # Pricing field
    price: Optional[float] = Field(
        default=0.00,
        ge=0,
        description="Test price (must be >= 0, max 2 decimal places)"
    )
    
    start_date: Optional[datetime] = Field(
        default=None,
        description="Test start date (optional)"
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="Test end date (optional)"
    )
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate that end_date >= start_date."""
        if v is not None and info.data.get('start_date') is not None:
            if v < info.data['start_date']:
                raise ValueError('end_date must be greater than or equal to start_date')
        return v
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Optional[float]) -> Optional[float]:
        """Validate price has max 2 decimal places."""
        if v is not None:
            # Check for max 2 decimal places
            if round(v, 2) != v:
                raise ValueError('price must have at most 2 decimal places')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name_en": "Midterm Exam",
                "name_uz": "Oraliq imtihon",
                "name_ru": "Промежуточный экзамен",
                "level_id": 1,
                "price": 9.99,
                "start_date": "2024-02-01T00:00:00",
                "end_date": "2024-02-15T23:59:59"
            }
        }
    )


class TestUpdate(BaseModel):
    """Request schema for updating a test."""
    # Multi-language fields
    name_en: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Test name in English (1-100 characters)"
    )
    name_uz: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Test name in Uzbek (1-100 characters)"
    )
    name_ru: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Test name in Russian (1-100 characters)"
    )
    
    # Legacy field (deprecated, kept for backward compatibility)
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Test name (legacy field, use name_en/name_uz/name_ru instead)"
    )
    
    # Level ID (optional for updates)
    level_id: Optional[int] = Field(
        default=None,
        description="Parent level ID (optional, allows moving test to different level)"
    )
    
    # Pricing field
    price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Test price (must be >= 0, max 2 decimal places)"
    )
    
    start_date: Optional[datetime] = Field(
        default=None,
        description="Test start date (optional)"
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="Test end date (optional)"
    )
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate that end_date >= start_date."""
        if v is not None and info.data.get('start_date') is not None:
            if v < info.data['start_date']:
                raise ValueError('end_date must be greater than or equal to start_date')
        return v
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Optional[float]) -> Optional[float]:
        """Validate price has max 2 decimal places."""
        if v is not None:
            # Check for max 2 decimal places
            if round(v, 2) != v:
                raise ValueError('price must have at most 2 decimal places')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name_en": "Updated Midterm Exam",
                "name_uz": "Yangilangan oraliq imtihon",
                "name_ru": "Обновленный промежуточный экзамен",
                "level_id": 2,
                "price": 12.50,
                "start_date": "2024-02-01T00:00:00",
                "end_date": "2024-02-20T23:59:59"
            }
        }
    )


class TestResponse(BaseModel):
    """Response schema for test data with nested level and subject."""
    id: int
    level_id: int
    name_en: str
    name_uz: str
    name_ru: str
    name: Optional[str] = None  # Legacy field for backward compatibility
    price: float
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    level: Optional[LevelWithSubjectResponse] = None  # Nested level with subject data
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "level_id": 1,
                "name_en": "Midterm Exam",
                "name_uz": "Oraliq imtihon",
                "name_ru": "Промежуточный экзамен",
                "name": "Midterm Exam",
                "price": 9.99,
                "start_date": "2024-02-01T00:00:00",
                "end_date": "2024-02-15T23:59:59",
                "level": {
                    "id": 1,
                    "subject_id": 1,
                    "name_en": "Grade 5",
                    "name_uz": "5-sinf",
                    "name_ru": "5 класс",
                    "name": "Grade 5",
                    "subject": {
                        "id": 1,
                        "name_en": "Mathematics",
                        "name_uz": "Matematika",
                        "name_ru": "Математика",
                        "name": "Mathematics",
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T10:30:00"
                    },
                    "created_at": "2024-01-15T10:30:00",
                    "updated_at": "2024-01-15T10:30:00"
                },
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )


# ============================================================================
# QUESTION OPTION SCHEMAS
# ============================================================================

class OptionInput(BaseModel):
    """Schema for question option input."""
    label: str = Field(
        pattern="^[A-J]$",
        description="Option label (A-J)"
    )
    
    # Multi-language fields
    text_en: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Option text in English (max 500 characters)"
    )
    text_uz: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Option text in Uzbek (max 500 characters)"
    )
    text_ru: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Option text in Russian (max 500 characters)"
    )
    
    # Legacy field (deprecated, kept for backward compatibility)
    text: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Option text (legacy field, use text_en/text_uz/text_ru instead)"
    )
    
    @field_validator('text_en', 'text_uz', 'text_ru', 'text', mode='before')
    @classmethod
    def convert_empty_to_none(cls, v):
        """Convert empty strings to None."""
        if v == "":
            return None
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "label": "A",
                "text_en": "This is the first option",
                "text_uz": "Bu birinchi variant",
                "text_ru": "Это первый вариант"
            }
        }
    )


class OptionResponse(BaseModel):
    """Response schema for question option data."""
    id: int
    question_id: int
    label: str
    text_en: str
    text_uz: str
    text_ru: str
    text: Optional[str] = None  # Legacy field for backward compatibility
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "question_id": 1,
                "label": "A",
                "text_en": "This is the first option",
                "text_uz": "Bu birinchi variant",
                "text_ru": "Это первый вариант",
                "text": "This is the first option",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )


# ============================================================================
# QUESTION SCHEMAS
# ============================================================================

class QuestionCreate(BaseModel):
    """Request schema for creating a question."""
    # Multi-language fields
    text_en: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Question text in English (1-1000 characters)"
    )
    text_uz: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Question text in Uzbek (1-1000 characters)"
    )
    text_ru: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Question text in Russian (1-1000 characters)"
    )
    
    # Legacy field (deprecated, kept for backward compatibility)
    text: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Question text (legacy field, use text_en/text_uz/text_ru instead)"
    )
    
    correct_answer: str = Field(
        pattern="^[A-J]$",
        description="Correct answer label (A-J)"
    )
    options: List[OptionInput] = Field(
        min_length=3,
        max_length=10,
        description="Question options (3-10 options required)"
    )
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v: List[OptionInput]) -> List[OptionInput]:
        """Validate that options have unique labels and text in each language."""
        labels = set()
        texts_en = set()
        texts_uz = set()
        texts_ru = set()

        for option in v:
            if option.label in labels:
                raise ValueError(f"Duplicate option label: {option.label}")
            
            # Only check for duplicates among non-None values
            if option.text_en is not None:
                if option.text_en in texts_en:
                    raise ValueError("Duplicate option text in English")
                texts_en.add(option.text_en)
            
            if option.text_uz is not None:
                if option.text_uz in texts_uz:
                    raise ValueError("Duplicate option text in Uzbek")
                texts_uz.add(option.text_uz)
            
            if option.text_ru is not None:
                if option.text_ru in texts_ru:
                    raise ValueError("Duplicate option text in Russian")
                texts_ru.add(option.text_ru)

            labels.add(option.label)

        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text_en": "What is 2 + 2?",
                "text_uz": "2 + 2 nechaga teng?",
                "text_ru": "Сколько будет 2 + 2?",
                "correct_answer": "A",
                "options": [
                    {
                        "label": "A",
                        "text_en": "4",
                        "text_uz": "4",
                        "text_ru": "4"
                    },
                    {
                        "label": "B",
                        "text_en": "5",
                        "text_uz": "5",
                        "text_ru": "5"
                    },
                    {
                        "label": "C",
                        "text_en": "3",
                        "text_uz": "3",
                        "text_ru": "3"
                    },
                    {
                        "label": "D",
                        "text_en": "6",
                        "text_uz": "6",
                        "text_ru": "6"
                    }
                ]
            }
        }
    )


class QuestionUpdate(BaseModel):
    """Request schema for updating a question."""
    # Multi-language fields
    text_en: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Question text in English (1-1000 characters)"
    )
    text_uz: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Question text in Uzbek (1-1000 characters)"
    )
    text_ru: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Question text in Russian (1-1000 characters)"
    )
    
    # Legacy field (deprecated, kept for backward compatibility)
    text: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Question text (legacy field, use text_en/text_uz/text_ru instead)"
    )
    
    correct_answer: str = Field(
        pattern="^[A-J]$",
        description="Correct answer label (A-J)"
    )
    options: List[OptionInput] = Field(
        min_length=3,
        max_length=10,
        description="Question options (3-10 options required)"
    )
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v: List[OptionInput]) -> List[OptionInput]:
        """Validate that options have unique labels and text in each language."""
        labels = set()
        texts_en = set()
        texts_uz = set()
        texts_ru = set()

        for option in v:
            if option.label in labels:
                raise ValueError(f"Duplicate option label: {option.label}")
            
            # Only check for duplicates among non-None values
            if option.text_en is not None:
                if option.text_en in texts_en:
                    raise ValueError("Duplicate option text in English")
                texts_en.add(option.text_en)
            
            if option.text_uz is not None:
                if option.text_uz in texts_uz:
                    raise ValueError("Duplicate option text in Uzbek")
                texts_uz.add(option.text_uz)
            
            if option.text_ru is not None:
                if option.text_ru in texts_ru:
                    raise ValueError("Duplicate option text in Russian")
                texts_ru.add(option.text_ru)

            labels.add(option.label)

        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text_en": "What is 3 + 3?",
                "text_uz": "3 + 3 nechaga teng?",
                "text_ru": "Сколько будет 3 + 3?",
                "correct_answer": "B",
                "options": [
                    {
                        "label": "A",
                        "text_en": "5",
                        "text_uz": "5",
                        "text_ru": "5"
                    },
                    {
                        "label": "B",
                        "text_en": "6",
                        "text_uz": "6",
                        "text_ru": "6"
                    },
                    {
                        "label": "C",
                        "text_en": "7",
                        "text_uz": "7",
                        "text_ru": "7"
                    },
                    {
                        "label": "D",
                        "text_en": "8",
                        "text_uz": "8",
                        "text_ru": "8"
                    }
                ]
            }
        }
    )


# ============================================================================
# IMAGE SCHEMAS
# ============================================================================

class ImageResponse(BaseModel):
    """Response schema for question image data."""
    id: int
    question_id: int
    image_path: str
    image_order: int
    original_filename: str
    file_size: int
    width: int
    height: int
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "question_id": 1,
                "image_path": "uploads/questions/1/abc123_1705315200.webp",
                "image_order": 1,
                "original_filename": "diagram.png",
                "file_size": 245678,
                "width": 1200,
                "height": 800,
                "created_at": "2024-01-15T10:00:00"
            }
        }
    )


class QuestionResponse(BaseModel):
    """Response schema for question data."""
    id: int
    test_id: int
    text_en: str
    text_uz: str
    text_ru: str
    text: Optional[str] = None  # Legacy field for backward compatibility
    correct_answer: str
    options: List[OptionResponse]
    images: Optional[List[ImageResponse]] = Field(default_factory=list, description="Attached images (0-2)")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "test_id": 1,
                "text_en": "What is 2 + 2?",
                "text_uz": "2 + 2 nechaga teng?",
                "text_ru": "Сколько будет 2 + 2?",
                "text": "What is 2 + 2?",
                "correct_answer": "A",
                "options": [
                    {
                        "id": 1,
                        "question_id": 1,
                        "label": "A",
                        "text_en": "4",
                        "text_uz": "4",
                        "text_ru": "4",
                        "text": "4",
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T10:30:00"
                    },
                    {
                        "id": 2,
                        "question_id": 1,
                        "label": "B",
                        "text_en": "5",
                        "text_uz": "5",
                        "text_ru": "5",
                        "text": "5",
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T10:30:00"
                    },
                    {
                        "id": 3,
                        "question_id": 1,
                        "label": "C",
                        "text_en": "3",
                        "text_uz": "3",
                        "text_ru": "3",
                        "text": "3",
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T10:30:00"
                    },
                    {
                        "id": 4,
                        "question_id": 1,
                        "label": "D",
                        "text_en": "6",
                        "text_uz": "6",
                        "text_ru": "6",
                        "text": "6",
                        "created_at": "2024-01-15T10:30:00",
                        "updated_at": "2024-01-15T10:30:00"
                    }
                ],
                "images": [],
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    )


# ============================================================================
# PAGINATION SCHEMAS
# ============================================================================

class PaginatedResponse(BaseModel):
    """Generic paginated response schema."""
    items: List
    total: int = Field(description="Total count of items")
    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Maximum items per page")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 100,
                "skip": 0,
                "limit": 50
            }
        }
    )


class SubjectListResponse(BaseModel):
    """Response schema for paginated subject list."""
    items: List[SubjectResponse]
    total: int
    skip: int
    limit: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 10,
                "skip": 0,
                "limit": 50
            }
        }
    )


class LevelListResponse(BaseModel):
    """Response schema for paginated level list."""
    items: List[LevelResponse]
    total: int
    skip: int
    limit: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 5,
                "skip": 0,
                "limit": 50
            }
        }
    )


class TestListResponse(BaseModel):
    """Response schema for paginated test list."""
    items: List[TestResponse]
    total: int
    skip: int
    limit: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 20,
                "skip": 0,
                "limit": 50
            }
        }
    )


class QuestionListResponse(BaseModel):
    """Response schema for paginated question list."""
    items: List[QuestionResponse]
    total: int
    skip: int
    limit: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 50,
                "skip": 0,
                "limit": 100
            }
        }
    )


class ImageListResponse(BaseModel):
    """Response schema for list of images."""
    items: List[ImageResponse]
    total: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 2
            }
        }
    )


# ============================================================================
# ERROR RESPONSE SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Response schema for error responses."""
    code: str = Field(description="Error code")
    message: str = Field(description="Error message")
    details: Optional[dict] = Field(default=None, description="Additional error details")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Subject name must be between 1 and 100 characters",
                "details": {"field": "name", "constraint": "length"}
            }
        }
    )

