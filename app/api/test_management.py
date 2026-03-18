"""
Test management API endpoints.

This module implements the test management endpoints for subjects, levels,
tests, and questions. All endpoints require admin authentication.
"""

from typing import Annotated, Optional, List
import json

from fastapi import APIRouter, Depends, status, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.database import get_db
from app.core.exceptions import (
    ResourceNotFoundError,
    ResourceConflictError,
    ValidationError,
)
from app.models.user import User
from app.schemas.test_management import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    SubjectListResponse,
    LevelCreate,
    LevelUpdate,
    LevelResponse,
    LevelListResponse,
    TestCreate,
    TestUpdate,
    TestResponse,
    TestListResponse,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionListResponse,
    ImageResponse,
    ImageListResponse,
    ErrorResponse,
)
from app.services.subject_service import SubjectService
from app.services.level_service import LevelService
from app.services.test_service import TestService
from app.services.question_service import QuestionService
from app.services.translation_service import TranslationService
from app.services.image_service import ImageService
from app.repositories.subject_repository import SubjectRepository
from app.repositories.level_repository import LevelRepository
from app.repositories.test_repository import TestRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.image_repository import ImageRepository
from app.services.audit_service import AuditService
from app.repositories.question_option_repository import QuestionOptionRepository

# Initialize router
router = APIRouter(prefix="/api/admin", tags=["test-management"])


# ============================================================================
# SUBJECT ENDPOINTS
# ============================================================================

@router.get(
    "/subjects",
    response_model=SubjectListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_subjects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    search: str = Query(None, description="Search term for filtering by name"),
    language: str = Query(None, description="Language code (en/uz/ru) for filtered response"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all subjects with pagination and search."""
    try:
        repo = SubjectRepository(db)
        translation_service = TranslationService()
        service = SubjectService(repo, translation_service)
        subjects, total = await service.list_subjects(skip=skip, limit=limit, search=search)
        return SubjectListResponse(
            items=subjects,
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/subjects",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subject(
    request: SubjectCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new subject."""
    try:
        repo = SubjectRepository(db)
        translation_service = TranslationService()
        service = SubjectService(repo, translation_service)
        subject = await service.create_subject(
            name_en=request.name_en,
            name_uz=request.name_uz,
            name_ru=request.name_ru,
            name=request.name
        )
        await db.commit()
        await db.refresh(subject)
        return subject
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ResourceConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/subjects/{subject_id}",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
)
async def get_subject(
    subject_id: int,
    language: str = Query(None, description="Language code (en/uz/ru) for filtered response"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a subject by ID."""
    try:
        repo = SubjectRepository(db)
        translation_service = TranslationService()
        service = SubjectService(repo, translation_service)
        subject = await service.get_subject(subject_id)
        return subject
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/subjects/{subject_id}",
    response_model=SubjectResponse,
    status_code=status.HTTP_200_OK,
)
async def update_subject(
    subject_id: int,
    request: SubjectUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a subject."""
    try:
        repo = SubjectRepository(db)
        translation_service = TranslationService()
        service = SubjectService(repo, translation_service)
        subject = await service.update_subject(
            subject_id,
            name_en=request.name_en,
            name_uz=request.name_uz,
            name_ru=request.name_ru,
            name=request.name
        )
        await db.commit()
        return subject
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ResourceConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/subjects/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_subject(
    subject_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a subject."""
    try:
        repo = SubjectRepository(db)
        translation_service = TranslationService()
        service = SubjectService(repo, translation_service)
        await service.delete_subject(subject_id)
        await db.commit()
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LEVEL ENDPOINTS
# ============================================================================

@router.get(
    "/subjects/{subject_id}/levels",
    response_model=LevelListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_levels(
    subject_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    search: str = Query(None, description="Search term for filtering by name"),
    language: str = Query(None, description="Language code (en/uz/ru) for filtered response"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List levels for a subject with search."""
    try:
        level_repo = LevelRepository(db)
        subject_repo = SubjectRepository(db)
        translation_service = TranslationService()
        service = LevelService(level_repo, subject_repo, translation_service)
        levels, total = await service.list_levels(subject_id, skip=skip, limit=limit, search=search)
        return LevelListResponse(
            items=levels,
            total=total,
            skip=skip,
            limit=limit
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get(
    "/levels",
    response_model=LevelListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_all_levels(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    search: str = Query(None, description="Search term for filtering by name"),
    language: str = Query(None, description="Language code (en/uz/ru) for filtered response"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all levels across all subjects with search."""
    try:
        level_repo = LevelRepository(db)
        subject_repo = SubjectRepository(db)
        translation_service = TranslationService()
        service = LevelService(level_repo, subject_repo, translation_service)
        levels, total = await service.list_all_levels(skip=skip, limit=limit, search=search)
        return LevelListResponse(
            items=levels,
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.post(
    "/subjects/{subject_id}/levels",
    response_model=LevelResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_level(
    subject_id: int,
    request: LevelCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new level."""
    try:
        level_repo = LevelRepository(db)
        subject_repo = SubjectRepository(db)
        translation_service = TranslationService()
        service = LevelService(level_repo, subject_repo, translation_service)
        level = await service.create_level(
            subject_id,
            name_en=request.name_en,
            name_uz=request.name_uz,
            name_ru=request.name_ru,
            name=request.name
        )
        await db.commit()
        await db.refresh(level)
        return level
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ResourceConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/levels/{level_id}",
    response_model=LevelResponse,
    status_code=status.HTTP_200_OK,
)
async def get_level_global(
    level_id: int,
    language: str = Query(None, description="Language code (en/uz/ru) for filtered response"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a level by ID (global endpoint)."""
    try:
        level_repo = LevelRepository(db)
        subject_repo = SubjectRepository(db)
        translation_service = TranslationService()
        service = LevelService(level_repo, subject_repo, translation_service)
        level = await service.get_level(level_id)
        return level
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/subjects/{subject_id}/levels/{level_id}",
    response_model=LevelResponse,
    status_code=status.HTTP_200_OK,
)
async def get_level(
    subject_id: int,
    level_id: int,
    language: str = Query(None, description="Language code (en/uz/ru) for filtered response"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a level by ID."""
    try:
        level_repo = LevelRepository(db)
        subject_repo = SubjectRepository(db)
        translation_service = TranslationService()
        service = LevelService(level_repo, subject_repo, translation_service)
        level = await service.get_level(level_id)
        return level
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/subjects/{subject_id}/levels/{level_id}",
    response_model=LevelResponse,
    status_code=status.HTTP_200_OK,
)
async def update_level(
    subject_id: int,
    level_id: int,
    request: LevelUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a level."""
    try:
        level_repo = LevelRepository(db)
        subject_repo = SubjectRepository(db)
        translation_service = TranslationService()
        service = LevelService(level_repo, subject_repo, translation_service)
        level = await service.update_level(
            level_id,
            name_en=request.name_en,
            name_uz=request.name_uz,
            name_ru=request.name_ru,
            name=request.name,
            subject_id=request.subject_id
        )
        await db.commit()
        return level
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ResourceConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/subjects/{subject_id}/levels/{level_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_level(
    subject_id: int,
    level_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a level."""
    try:
        level_repo = LevelRepository(db)
        subject_repo = SubjectRepository(db)
        translation_service = TranslationService()
        service = LevelService(level_repo, subject_repo, translation_service)
        await service.delete_level(level_id)
        await db.commit()
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TEST ENDPOINTS
# ============================================================================

# Global test endpoints (without level_id requirement)
@router.get(
    "/tests",
    response_model=TestListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_all_tests(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    search: str = Query(None, description="Search term for filtering by name (searches all languages)"),
    subject_id: int = Query(None, description="Filter by subject ID"),
    level_id: int = Query(None, description="Filter by level ID"),
    min_price: float = Query(None, ge=0, description="Minimum price filter"),
    max_price: float = Query(None, ge=0, description="Maximum price filter"),
    start_date_from: str = Query(None, description="Filter tests starting from this date (ISO format)"),
    start_date_to: str = Query(None, description="Filter tests starting before this date (ISO format)"),
    language: str = Query(None, description="Language code (en/uz/ru) for filtered response"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all tests with pagination, search, and filters."""
    try:
        test_repo = TestRepository(db)
        level_repo = LevelRepository(db)
        translation_service = TranslationService()
        service = TestService(test_repo, level_repo, translation_service)
        
        # If level_id is provided, use the existing method
        if level_id:
            tests, total = await service.list_tests(
                level_id, 
                skip=skip, 
                limit=limit, 
                search=search,
                min_price=min_price,
                max_price=max_price,
                start_date_from=start_date_from,
                start_date_to=start_date_to
            )
        else:
            # List all tests across all levels
            tests, total = await service.list_all_tests(
                skip=skip, 
                limit=limit, 
                search=search,
                subject_id=subject_id,
                min_price=min_price,
                max_price=max_price,
                start_date_from=start_date_from,
                start_date_to=start_date_to
            )
        
        return TestListResponse(
            items=tests,
            total=total,
            skip=skip,
            limit=limit
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/tests",
    response_model=TestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_test_global(
    request: TestCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new test (global endpoint)."""
    try:
        test_repo = TestRepository(db)
        level_repo = LevelRepository(db)
        translation_service = TranslationService()
        service = TestService(test_repo, level_repo, translation_service)
        test = await service.create_test(
            request.level_id,
            name_en=request.name_en,
            name_uz=request.name_uz,
            name_ru=request.name_ru,
            name=request.name,
            price=request.price,
            start_date=request.start_date,
            end_date=request.end_date
        )
        await db.commit()
        # Fetch the test again with relationships loaded to avoid DetachedInstanceError
        test = await test_repo.get_by_id(test.id)
        return test
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ResourceConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/tests/{test_id}",
    response_model=TestResponse,
    status_code=status.HTTP_200_OK,
)
async def get_test_global(
    test_id: int,
    language: str = Query(None, description="Language code (en/uz/ru) for filtered response"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a test by ID (global endpoint)."""
    try:
        test_repo = TestRepository(db)
        level_repo = LevelRepository(db)
        translation_service = TranslationService()
        service = TestService(test_repo, level_repo, translation_service)
        test = await service.get_test(test_id)
        return test
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/tests/{test_id}",
    response_model=TestResponse,
    status_code=status.HTTP_200_OK,
)
async def update_test_global(
    test_id: int,
    request: TestUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a test (global endpoint)."""
    try:
        test_repo = TestRepository(db)
        level_repo = LevelRepository(db)
        translation_service = TranslationService()
        service = TestService(test_repo, level_repo, translation_service)
        test = await service.update_test(
            test_id,
            name_en=request.name_en,
            name_uz=request.name_uz,
            name_ru=request.name_ru,
            name=request.name,
            price=request.price,
            start_date=request.start_date,
            end_date=request.end_date,
            level_id=request.level_id
        )
        await db.commit()
        return test
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ResourceConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/tests/{test_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_test_global(
    test_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a test (global endpoint)."""
    try:
        test_repo = TestRepository(db)
        level_repo = LevelRepository(db)
        translation_service = TranslationService()
        service = TestService(test_repo, level_repo, translation_service)
        await service.delete_test(test_id)
        await db.commit()
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Level-specific test endpoints
@router.get(
    "/levels/{level_id}/tests",
    response_model=TestListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_tests(
    level_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    search: str = Query(None, description="Search term for filtering by name (searches all languages)"),
    language: str = Query(None, description="Language code (en/uz/ru) for filtered response"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List tests for a level with search."""
    try:
        test_repo = TestRepository(db)
        level_repo = LevelRepository(db)
        translation_service = TranslationService()
        service = TestService(test_repo, level_repo, translation_service)
        tests, total = await service.list_tests(level_id, skip=skip, limit=limit, search=search)
        return TestListResponse(
            items=tests,
            total=total,
            skip=skip,
            limit=limit
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/levels/{level_id}/tests",
    response_model=TestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_test(
    level_id: int,
    request: TestCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new test."""
    try:
        test_repo = TestRepository(db)
        level_repo = LevelRepository(db)
        translation_service = TranslationService()
        service = TestService(test_repo, level_repo, translation_service)
        test = await service.create_test(
            level_id,
            name_en=request.name_en,
            name_uz=request.name_uz,
            name_ru=request.name_ru,
            name=request.name,
            price=request.price,
            start_date=request.start_date,
            end_date=request.end_date
        )
        await db.commit()
        # Fetch the test again with relationships loaded to avoid DetachedInstanceError
        test = await test_repo.get_by_id(test.id)
        return test
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ResourceConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/levels/{level_id}/tests/{test_id}",
    response_model=TestResponse,
    status_code=status.HTTP_200_OK,
)
async def get_test(
    level_id: int,
    test_id: int,
    language: str = Query(None, description="Language code (en/uz/ru) for filtered response"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a test by ID."""
    try:
        test_repo = TestRepository(db)
        level_repo = LevelRepository(db)
        translation_service = TranslationService()
        service = TestService(test_repo, level_repo, translation_service)
        test = await service.get_test(test_id)
        return test
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/levels/{level_id}/tests/{test_id}",
    response_model=TestResponse,
    status_code=status.HTTP_200_OK,
)
async def update_test(
    level_id: int,
    test_id: int,
    request: TestUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a test."""
    try:
        test_repo = TestRepository(db)
        level_repo = LevelRepository(db)
        translation_service = TranslationService()
        service = TestService(test_repo, level_repo, translation_service)
        test = await service.update_test(
            test_id,
            name_en=request.name_en,
            name_uz=request.name_uz,
            name_ru=request.name_ru,
            name=request.name,
            price=request.price,
            start_date=request.start_date,
            end_date=request.end_date
        )
        await db.commit()
        return test
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ResourceConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/levels/{level_id}/tests/{test_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_test(
    level_id: int,
    test_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a test."""
    try:
        test_repo = TestRepository(db)
        level_repo = LevelRepository(db)
        translation_service = TranslationService()
        service = TestService(test_repo, level_repo, translation_service)
        await service.delete_test(test_id)
        await db.commit()
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# QUESTION ENDPOINTS
# ============================================================================

@router.get(
    "/tests/{test_id}/questions",
    response_model=QuestionListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_questions(
    test_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=200, description="Maximum records to return"),
    search: str = Query(None, description="Search term for filtering by question text"),
    language: str = Query(None, description="Language code for filtering (en, uz, ru)"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List questions for a test with search."""
    try:
        question_repo = QuestionRepository(db)
        option_repo = QuestionOptionRepository(db)
        test_repo = TestRepository(db)
        translation_service = TranslationService()
        service = QuestionService(question_repo, option_repo, test_repo, translation_service)
        questions, total = await service.list_questions(test_id, skip=skip, limit=limit, search=search)
        return QuestionListResponse(
            items=questions,
            total=total,
            skip=skip,
            limit=limit
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/tests/{test_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_question(
    test_id: int,
    text_en: Optional[str] = Form(None),
    text_uz: Optional[str] = Form(None),
    text_ru: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    correct_answer: str = Form(...),
    options: str = Form(...),  # JSON string of options
    image1: Optional[UploadFile] = File(None),
    image2: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new question with optional image uploads.
    
    Accepts multipart/form-data with:
    - Question data as form fields (text_en, text_uz, text_ru, correct_answer)
    - Options as JSON string
    - Up to 2 optional image files (image1, image2)
    """
    try:
        # Parse options from JSON string
        try:
            options_list = json.loads(options)
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON format for options")
        
        # Create question
        question_repo = QuestionRepository(db)
        option_repo = QuestionOptionRepository(db)
        test_repo = TestRepository(db)
        translation_service = TranslationService()
        service = QuestionService(question_repo, option_repo, test_repo, translation_service)
        question = await service.create_question(
            test_id,
            text_en=text_en,
            text_uz=text_uz,
            text_ru=text_ru,
            text=text,
            correct_answer=correct_answer,
            options=[{
                "label": opt["label"],
                "text_en": opt.get("text_en"),
                "text_uz": opt.get("text_uz"),
                "text_ru": opt.get("text_ru"),
                "text": opt.get("text")
            } for opt in options_list]
        )
        
        # Handle image uploads if provided
        image_repo = ImageRepository(db)
        image_service = ImageService(image_repo)
        
        if image1:
            await image_service.save_image(question.id, image1, order=1)
        
        if image2:
            await image_service.save_image(question.id, image2, order=2)
        
        await db.commit()
        
        # Reload the question with eagerly loaded options and images
        question_with_relations = await question_repo.get_by_id(question.id)
        return question_with_relations
    except ValidationError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=e.message)
    except ResourceNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/tests/{test_id}/questions/{question_id}",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_question(
    test_id: int,
    question_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a question by ID."""
    try:
        question_repo = QuestionRepository(db)
        option_repo = QuestionOptionRepository(db)
        test_repo = TestRepository(db)
        translation_service = TranslationService()
        service = QuestionService(question_repo, option_repo, test_repo, translation_service)
        question = await service.get_question(question_id)
        return question
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/tests/{test_id}/questions/{question_id}",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
)
async def update_question(
    test_id: int,
    question_id: int,
    text_en: Optional[str] = Form(None),
    text_uz: Optional[str] = Form(None),
    text_ru: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    correct_answer: str = Form(...),
    options: str = Form(...),  # JSON string of options
    image1: Optional[UploadFile] = File(None),
    image2: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a question with optional image uploads.
    
    Accepts multipart/form-data with:
    - Question data as form fields (text_en, text_uz, text_ru, correct_answer)
    - Options as JSON string
    - Up to 2 optional image files (image1, image2)
    
    When new images are provided, old images are automatically deleted.
    """
    try:
        # Parse options from JSON string
        try:
            options_list = json.loads(options)
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON format for options")
        
        # Initialize services
        question_repo = QuestionRepository(db)
        option_repo = QuestionOptionRepository(db)
        test_repo = TestRepository(db)
        image_repo = ImageRepository(db)
        translation_service = TranslationService()
        question_service = QuestionService(question_repo, option_repo, test_repo, translation_service)
        image_service = ImageService(image_repo)
        
        # Update question
        question = await question_service.update_question(
            question_id,
            text_en=text_en,
            text_uz=text_uz,
            text_ru=text_ru,
            text=text,
            correct_answer=correct_answer,
            options=[{
                "label": opt["label"],
                "text_en": opt.get("text_en"),
                "text_uz": opt.get("text_uz"),
                "text_ru": opt.get("text_ru"),
                "text": opt.get("text")
            } for opt in options_list]
        )
        
        # Handle image uploads if provided
        # If new images are provided, delete old images first
        if image1 or image2:
            existing_images = await image_repo.get_by_question_id(question_id)
            for img in existing_images:
                await image_service.delete_image(img.id)
        
        # Upload new images
        if image1:
            await image_service.save_image(question_id, image1, order=1)
        
        if image2:
            await image_service.save_image(question_id, image2, order=2)
        
        await db.commit()
        
        # Reload question with all relations
        updated_question = await question_repo.get_by_id(question_id)
        return updated_question
    except ValidationError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=e.message)
    except ResourceNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/tests/{test_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_question(
    test_id: int,
    question_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a question."""
    try:
        question_repo = QuestionRepository(db)
        option_repo = QuestionOptionRepository(db)
        test_repo = TestRepository(db)
        translation_service = TranslationService()
        service = QuestionService(question_repo, option_repo, test_repo, translation_service)
        await service.delete_question(question_id)
        await db.commit()
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# IMAGE ENDPOINTS
# ============================================================================

@router.get(
    "/questions/{question_id}/images",
    response_model=ImageListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_question_images(
    question_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all images for a question.
    
    Returns a list of images ordered by image_order (1, 2).
    """
    try:
        image_repo = ImageRepository(db)
        images = await image_repo.get_by_question_id(question_id)
        
        return ImageListResponse(
            items=images,
            total=len(images)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/images/{image_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_image(
    image_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an image by ID.
    
    Removes the image file from the filesystem and deletes the metadata from the database.
    """
    try:
        image_repo = ImageRepository(db)
        image_service = ImageService(image_repo)
        
        await image_service.delete_image(image_id)
        await db.commit()
        
        return {"message": "Image deleted successfully"}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
