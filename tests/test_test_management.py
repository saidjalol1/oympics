"""
Tests for test management system (subjects, levels, tests, questions).

This module contains unit and integration tests for the test management
API endpoints and services.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.subject import Subject
from app.models.level import Level
from app.models.test import Test
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.repositories.subject_repository import SubjectRepository
from app.repositories.level_repository import LevelRepository
from app.repositories.test_repository import TestRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.question_option_repository import QuestionOptionRepository
from app.services.subject_service import SubjectService
from app.services.level_service import LevelService
from app.services.test_service import TestService
from app.services.question_service import QuestionService
from app.services.translation_service import TranslationService
from app.core.exceptions import (
    ResourceNotFoundError,
    ResourceConflictError,
    ValidationError,
)


@pytest_asyncio.fixture
async def db():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


# ============================================================================
# SUBJECT SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_subject(db: AsyncSession):
    """Test creating a subject."""
    repo = SubjectRepository(db)
    translation_service = TranslationService()
    service = SubjectService(repo, translation_service)
    
    subject = await service.create_subject(name="Mathematics")
    
    assert subject.id is not None
    assert subject.name == "Mathematics"
    assert subject.created_at is not None


@pytest.mark.asyncio
async def test_create_subject_duplicate_name(db: AsyncSession):
    """Test that duplicate subject names are rejected."""
    repo = SubjectRepository(db)
    translation_service = TranslationService()
    service = SubjectService(repo, translation_service)
    
    await service.create_subject(name="Mathematics")
    
    with pytest.raises(ResourceConflictError):
        await service.create_subject(name="Mathematics")


@pytest.mark.asyncio
async def test_create_subject_invalid_name_empty(db: AsyncSession):
    """Test that empty subject names are rejected."""
    repo = SubjectRepository(db)
    translation_service = TranslationService()
    service = SubjectService(repo, translation_service)
    
    with pytest.raises(ValidationError):
        await service.create_subject(name="")


@pytest.mark.asyncio
async def test_create_subject_invalid_name_too_long(db: AsyncSession):
    """Test that subject names > 100 chars are rejected."""
    repo = SubjectRepository(db)
    translation_service = TranslationService()
    service = SubjectService(repo, translation_service)
    
    long_name = "a" * 101
    with pytest.raises(ValidationError):
        await service.create_subject(name=long_name)


@pytest.mark.asyncio
async def test_get_subject(db: AsyncSession):
    """Test retrieving a subject by ID."""
    repo = SubjectRepository(db)
    translation_service = TranslationService()
    service = SubjectService(repo, translation_service)
    
    created = await service.create_subject(name="Mathematics")
    retrieved = await service.get_subject(created.id)
    
    assert retrieved.id == created.id
    assert retrieved.name == "Mathematics"


@pytest.mark.asyncio
async def test_get_subject_not_found(db: AsyncSession):
    """Test that retrieving non-existent subject raises error."""
    repo = SubjectRepository(db)
    translation_service = TranslationService()
    service = SubjectService(repo, translation_service)
    
    with pytest.raises(ResourceNotFoundError):
        await service.get_subject(999)


@pytest.mark.asyncio
async def test_list_subjects(db: AsyncSession):
    """Test listing subjects with pagination."""
    repo = SubjectRepository(db)
    translation_service = TranslationService()
    service = SubjectService(repo, translation_service)
    
    await service.create_subject(name="Mathematics")
    await service.create_subject(name="Physics")
    await service.create_subject(name="Chemistry")
    
    subjects, total = await service.list_subjects(skip=0, limit=10)
    
    assert len(subjects) == 3
    assert total == 3


@pytest.mark.asyncio
async def test_update_subject(db: AsyncSession):
    """Test updating a subject."""
    repo = SubjectRepository(db)
    translation_service = TranslationService()
    service = SubjectService(repo, translation_service)
    
    created = await service.create_subject(name="Mathematics")
    updated = await service.update_subject(created.id, name="Advanced Mathematics")
    
    assert updated.name == "Advanced Mathematics"


@pytest.mark.asyncio
async def test_delete_subject(db: AsyncSession):
    """Test deleting a subject."""
    repo = SubjectRepository(db)
    translation_service = TranslationService()
    service = SubjectService(repo, translation_service)
    
    created = await service.create_subject(name="Mathematics")
    await service.delete_subject(created.id)
    
    with pytest.raises(ResourceNotFoundError):
        await service.get_subject(created.id)


# ============================================================================
# LEVEL SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_level(db: AsyncSession):
    """Test creating a level."""
    subject_repo = SubjectRepository(db)
    level_repo = LevelRepository(db)
    translation_service = TranslationService()
    subject_service = SubjectService(subject_repo, translation_service)
    level_service = LevelService(level_repo, subject_repo, translation_service)
    
    subject = await subject_service.create_subject(name="Mathematics")
    level = await level_service.create_level(subject.id, name="Grade 5")
    
    assert level.id is not None
    assert level.subject_id == subject.id
    assert level.name == "Grade 5"


@pytest.mark.asyncio
async def test_create_level_duplicate_name_in_subject(db: AsyncSession):
    """Test that duplicate level names within subject are rejected."""
    subject_repo = SubjectRepository(db)
    level_repo = LevelRepository(db)
    translation_service = TranslationService()
    subject_service = SubjectService(subject_repo, translation_service)
    level_service = LevelService(level_repo, subject_repo, translation_service)
    
    subject = await subject_service.create_subject(name="Mathematics")
    await level_service.create_level(subject.id, name="Grade 5")
    
    with pytest.raises(ResourceConflictError):
        await level_service.create_level(subject.id, name="Grade 5")


@pytest.mark.asyncio
async def test_create_level_subject_not_found(db: AsyncSession):
    """Test that creating level for non-existent subject raises error."""
    level_repo = LevelRepository(db)
    subject_repo = SubjectRepository(db)
    translation_service = TranslationService()
    level_service = LevelService(level_repo, subject_repo, translation_service)
    
    with pytest.raises(ResourceNotFoundError):
        await level_service.create_level(999, name="Grade 5")


# ============================================================================
# TEST SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_test(db: AsyncSession):
    """Test creating a test."""
    subject_repo = SubjectRepository(db)
    level_repo = LevelRepository(db)
    test_repo = TestRepository(db)
    translation_service = TranslationService()
    
    subject_service = SubjectService(subject_repo, translation_service)
    level_service = LevelService(level_repo, subject_repo, translation_service)
    test_service = TestService(test_repo, level_repo, translation_service)
    
    subject = await subject_service.create_subject(name="Mathematics")
    level = await level_service.create_level(subject.id, name="Grade 5")
    
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=7)
    
    test = await test_service.create_test(
        level.id,
        name="Midterm Exam",
        start_date=start_date,
        end_date=end_date
    )
    
    assert test.id is not None
    assert test.level_id == level.id
    assert test.name == "Midterm Exam"


@pytest.mark.asyncio
async def test_create_test_invalid_date_range(db: AsyncSession):
    """Test that invalid date ranges are rejected."""
    subject_repo = SubjectRepository(db)
    level_repo = LevelRepository(db)
    test_repo = TestRepository(db)
    translation_service = TranslationService()
    
    subject_service = SubjectService(subject_repo, translation_service)
    level_service = LevelService(level_repo, subject_repo, translation_service)
    test_service = TestService(test_repo, level_repo, translation_service)
    
    subject = await subject_service.create_subject(name="Mathematics")
    level = await level_service.create_level(subject.id, name="Grade 5")
    
    start_date = datetime.now(timezone.utc)
    end_date = start_date - timedelta(days=7)  # End before start
    
    with pytest.raises(ValidationError):
        await test_service.create_test(
            level.id,
            name="Midterm Exam",
            start_date=start_date,
            end_date=end_date
        )


# ============================================================================
# QUESTION SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_question(db: AsyncSession):
    """Test creating a question."""
    subject_repo = SubjectRepository(db)
    level_repo = LevelRepository(db)
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)
    translation_service = TranslationService()
    
    subject_service = SubjectService(subject_repo, translation_service)
    level_service = LevelService(level_repo, subject_repo, translation_service)
    test_service = TestService(test_repo, level_repo, translation_service)
    question_service = QuestionService(question_repo, option_repo, test_repo, translation_service)
    
    subject = await subject_service.create_subject(
        name_en="Mathematics",
        name_uz="Matematika",
        name_ru="Математика"
    )
    level = await level_service.create_level(
        subject.id,
        name_en="Grade 5",
        name_uz="5-sinf",
        name_ru="5 класс"
    )
    test = await test_service.create_test(
        level.id,
        name_en="Midterm Exam",
        name_uz="Oraliq imtihon",
        name_ru="Промежуточный экзамен"
    )
    
    options = [
        {"label": "A", "text_en": "4", "text_uz": "4", "text_ru": "4"},
        {"label": "B", "text_en": "5", "text_uz": "5", "text_ru": "5"},
        {"label": "C", "text_en": "3", "text_uz": "3", "text_ru": "3"},
        {"label": "D", "text_en": "6", "text_uz": "6", "text_ru": "6"},
    ]
    
    question = await question_service.create_question(
        test.id,
        text_en="What is 2 + 2?",
        text_uz="2 + 2 nechaga teng?",
        text_ru="Сколько будет 2 + 2?",
        correct_answer="A",
        options=options
    )
    
    assert question.id is not None
    assert question.test_id == test.id
    assert question.text_en == "What is 2 + 2?"
    assert question.text_uz == "2 + 2 nechaga teng?"
    assert question.text_ru == "Сколько будет 2 + 2?"
    assert question.correct_answer == "A"
    assert len(question.options) == 4


@pytest.mark.asyncio
async def test_create_question_invalid_option_count(db: AsyncSession):
    """Test that invalid option counts are rejected."""
    subject_repo = SubjectRepository(db)
    level_repo = LevelRepository(db)
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)
    translation_service = TranslationService()
    
    subject_service = SubjectService(subject_repo, translation_service)
    level_service = LevelService(level_repo, subject_repo, translation_service)
    test_service = TestService(test_repo, level_repo, translation_service)
    question_service = QuestionService(question_repo, option_repo, test_repo, translation_service)
    
    subject = await subject_service.create_subject(
        name_en="Mathematics",
        name_uz="Matematika",
        name_ru="Математика"
    )
    level = await level_service.create_level(
        subject.id,
        name_en="Grade 5",
        name_uz="5-sinf",
        name_ru="5 класс"
    )
    test = await test_service.create_test(
        level.id,
        name_en="Midterm Exam",
        name_uz="Oraliq imtihon",
        name_ru="Промежуточный экзамен"
    )
    
    options = [
        {"label": "A", "text_en": "4", "text_uz": "4", "text_ru": "4"},
        {"label": "B", "text_en": "5", "text_uz": "5", "text_ru": "5"},
    ]  # Only 2 options, need 3-10
    
    with pytest.raises(ValidationError):
        await question_service.create_question(
            test.id,
            text_en="What is 2 + 2?",
            text_uz="2 + 2 nechaga teng?",
            text_ru="Сколько будет 2 + 2?",
            correct_answer="A",
            options=options
        )


@pytest.mark.asyncio
async def test_create_question_invalid_correct_answer(db: AsyncSession):
    """Test that invalid correct answers are rejected."""
    subject_repo = SubjectRepository(db)
    level_repo = LevelRepository(db)
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)
    translation_service = TranslationService()
    
    subject_service = SubjectService(subject_repo, translation_service)
    level_service = LevelService(level_repo, subject_repo, translation_service)
    test_service = TestService(test_repo, level_repo, translation_service)
    question_service = QuestionService(question_repo, option_repo, test_repo, translation_service)
    
    subject = await subject_service.create_subject(
        name_en="Mathematics",
        name_uz="Matematika",
        name_ru="Математика"
    )
    level = await level_service.create_level(
        subject.id,
        name_en="Grade 5",
        name_uz="5-sinf",
        name_ru="5 класс"
    )
    test = await test_service.create_test(
        level.id,
        name_en="Midterm Exam",
        name_uz="Oraliq imtihon",
        name_ru="Промежуточный экзамен"
    )
    
    options = [
        {"label": "A", "text_en": "4", "text_uz": "4", "text_ru": "4"},
        {"label": "B", "text_en": "5", "text_uz": "5", "text_ru": "5"},
        {"label": "C", "text_en": "3", "text_uz": "3", "text_ru": "3"},
        {"label": "D", "text_en": "6", "text_uz": "6", "text_ru": "6"},
    ]
    
    with pytest.raises(ValidationError):
        await question_service.create_question(
            test.id,
            text_en="What is 2 + 2?",
            text_uz="2 + 2 nechaga teng?",
            text_ru="Сколько будет 2 + 2?",
            correct_answer="E",  # Invalid - not in options
            options=options
        )


# ============================================================================
# IMAGE SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_question_with_images(db: AsyncSession):
    """Test creating a question with image upload functionality."""
    from app.repositories.image_repository import ImageRepository
    from app.services.image_service import ImageService
    from io import BytesIO
    from PIL import Image
    from fastapi import UploadFile
    
    # Create test data
    subject_repo = SubjectRepository(db)
    level_repo = LevelRepository(db)
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)
    image_repo = ImageRepository(db)
    translation_service = TranslationService()
    
    # Create subject, level, test
    subject_service = SubjectService(subject_repo, translation_service)
    subject = await subject_service.create_subject(
        name_en="Mathematics",
        name_uz="Matematika",
        name_ru="Математика"
    )
    
    level_service = LevelService(level_repo, subject_repo, translation_service)
    level = await level_service.create_level(
        subject.id,
        name_en="Grade 5",
        name_uz="5-sinf",
        name_ru="5 класс"
    )
    
    test_service = TestService(test_repo, level_repo, translation_service)
    test = await test_service.create_test(
        level.id,
        name_en="Midterm",
        name_uz="Oraliq",
        name_ru="Промежуточный",
        price=0.00
    )
    
    # Create question
    question_service = QuestionService(question_repo, option_repo, test_repo, translation_service)
    question = await question_service.create_question(
        test.id,
        text_en="What is 2+2?",
        text_uz="2+2 nechaga teng?",
        text_ru="Сколько будет 2+2?",
        correct_answer="A",
        options=[
            {"label": "A", "text_en": "4", "text_uz": "4", "text_ru": "4"},
            {"label": "B", "text_en": "5", "text_uz": "5", "text_ru": "5"},
            {"label": "C", "text_en": "3", "text_uz": "3", "text_ru": "3"},
        ]
    )
    
    # Create a test image
    img = Image.new('RGB', (200, 200), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Create UploadFile mock
    from starlette.datastructures import UploadFile as StarletteUploadFile
    upload_file = StarletteUploadFile(filename="test_image.png", file=img_bytes, headers={"content-type": "image/png"})
    
    # Test image service
    image_service = ImageService(image_repo)
    
    # Validate image
    width, height = await image_service.validate_image(upload_file)
    assert width == 200
    assert height == 200
    
    # Note: We can't fully test save_image without a real filesystem
    # but we've validated the core validation logic works
    
    print("✓ Image validation test passed")


@pytest.mark.asyncio
async def test_image_validation_size_limit(db: AsyncSession):
    """Test that images over 5MB are rejected."""
    from app.repositories.image_repository import ImageRepository
    from app.services.image_service import ImageService
    from io import BytesIO
    from starlette.datastructures import UploadFile as StarletteUploadFile
    
    image_repo = ImageRepository(db)
    image_service = ImageService(image_repo)
    
    # Create a file that's too large (simulate with seek)
    large_file = BytesIO(b"x" * (6 * 1024 * 1024))  # 6MB
    
    upload_file = StarletteUploadFile(filename="large.png", file=large_file, headers={"content-type": "image/png"})
    
    with pytest.raises(ValidationError) as exc_info:
        await image_service.validate_image(upload_file)
    
    assert "exceeds maximum allowed size" in str(exc_info.value)
    print("✓ Image size validation test passed")


@pytest.mark.asyncio
async def test_image_validation_format(db: AsyncSession):
    """Test that invalid image formats are rejected."""
    from app.repositories.image_repository import ImageRepository
    from app.services.image_service import ImageService
    from io import BytesIO
    from starlette.datastructures import UploadFile as StarletteUploadFile
    
    image_repo = ImageRepository(db)
    image_service = ImageService(image_repo)
    
    # Create a non-image file
    text_file = BytesIO(b"This is not an image")
    
    upload_file = StarletteUploadFile(filename="test.txt", file=text_file, headers={"content-type": "text/plain"})
    
    with pytest.raises(ValidationError) as exc_info:
        await image_service.validate_image(upload_file)
    
    assert "Unsupported image format" in str(exc_info.value)
    print("✓ Image format validation test passed")
