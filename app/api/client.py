"""Client-facing API endpoints for test management.

This module provides public API endpoints for clients to:
- Browse subjects and levels
- Search and filter tests
- Submit test answers and get results
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.subject import Subject
from app.models.level import Level
from app.models.test import Test
from app.models.question import Question
from app.models.user import User
from app.repositories.subject_repository import SubjectRepository
from app.repositories.level_repository import LevelRepository
from app.repositories.test_repository import TestRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.question_option_repository import QuestionOptionRepository
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/client", tags=["client"])


def get_language_from_header(request: Request) -> str:
    """Extract language code from Accept-Language header.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Language code (en, uz, ru), defaults to 'en'
    """
    accept_lang = request.headers.get("accept-language", "en")
    # Parse first language code (e.g., "en-US,en;q=0.9" -> "en")
    lang_code = accept_lang.split(",")[0].split("-")[0].lower()
    # Validate it's one of supported languages
    if lang_code not in ["en", "uz", "ru"]:
        lang_code = "en"
    return lang_code


def get_name_column(model, language: str):
    """Get the appropriate name column for the language.
    
    Args:
        model: SQLAlchemy model class
        language: Language code (en, uz, ru)
        
    Returns:
        The name column for the specified language, defaults to name_en
    """
    return getattr(model, f'name_{language}', model.name_en)


# Request/Response schemas
class AnswerItem(BaseModel):
    """Individual answer item."""
    question_id: int
    answer: str


class SubmitAnswersRequest(BaseModel):
    """Request body for submitting answers."""
    answers: List[AnswerItem]


class AnswerResult(BaseModel):
    """Individual answer result."""
    question_id: int
    submitted_answer: str
    correct_answer: str
    is_correct: bool


class SubmitAnswersResponse(BaseModel):
    """Response for submitted answers."""
    test_id: int
    total_questions: int
    correct_answers: int
    score: int
    results: List[AnswerResult]


class QuestionOptionResponse(BaseModel):
    """Question option in test detail response."""
    id: int
    label: str
    text: str


class QuestionDetailResponse(BaseModel):
    """Question with options in test detail response."""
    id: int
    text: str
    correct_answer: str
    options: List[QuestionOptionResponse]


class TestDetailResponse(BaseModel):
    """Detailed test response with all questions and options."""
    id: int
    name: str
    price: float
    level_id: int
    level_name: Optional[str]
    subject_id: Optional[int]
    questions: List[QuestionDetailResponse]


@router.get("/subjects", response_model=List[dict])
async def get_subjects(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get all subjects.
    
    Language is extracted from Accept-Language header (defaults to 'en').
    
    Returns:
        List of subjects with id and name in requested language
    """
    language = get_language_from_header(request)
    
    # Select only id and the requested language name column
    name_column = getattr(Subject, f'name_{language}')
    stmt = select(Subject.id, name_column.label('name')).limit(1000)
    
    result = await db.execute(stmt)
    subjects = result.all()
    
    return [
        {
            "id": s.id,
            "name": s.name
        }
        for s in subjects
    ]


@router.get("/subjects/{subject_id}/levels", response_model=List[dict])
async def get_levels_for_subject(
    subject_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get levels for a subject.
    
    Args:
        subject_id: Subject ID
        
    Language is extracted from Accept-Language header (defaults to 'en').
        
    Returns:
        List of levels with id and name in requested language
    """
    language = get_language_from_header(request)
    
    # Select only id and the requested language name column
    name_column = getattr(Level, f'name_{language}')
    stmt = select(Level.id, name_column.label('name')).where(
        Level.subject_id == subject_id
    ).limit(1000)
    
    result = await db.execute(stmt)
    levels = result.all()
    
    return [
        {
            "id": l.id,
            "name": l.name
        }
        for l in levels
    ]


@router.get("/tests", response_model=dict)
async def get_tests(
    request: Request,
    subject_id: Optional[int] = Query(None),
    level_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get tests with filtering and pagination.
    
    Query parameters:
        subject_id: Filter by subject ID (optional)
        level_id: Filter by level ID (optional)
        min_price: Filter by minimum price (optional)
        max_price: Filter by maximum price (optional)
        start_date: Filter by start date (ISO format, optional)
        end_date: Filter by end date (ISO format, optional)
        skip: Pagination skip (default: 0)
        limit: Pagination limit (default: 10, max: 100)
        
    Language is extracted from Accept-Language header (defaults to 'en').
        
    Returns:
        Paginated list of tests with metadata in requested language
    """
    language = get_language_from_header(request)
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)
    
    # If level_id is provided, use it; otherwise use subject_id for filtering
    if level_id:
        tests, total = await test_repo.list_by_level(
            level_id=level_id,
            skip=skip,
            limit=limit,
            min_price=min_price,
            max_price=max_price,
            start_date_from=start_date,
            start_date_to=end_date
        )
    else:
        tests, total = await test_repo.list_all(
            skip=skip,
            limit=limit,
            subject_id=subject_id,
            min_price=min_price,
            max_price=max_price,
            start_date_from=start_date,
            start_date_to=end_date
        )
    
    # Build response with question counts
    test_list = []
    for test in tests:
        _, question_count = await question_repo.list_by_test(test.id, skip=0, limit=1)
        
        # Select name based on language
        test_name = getattr(test, f'name_{language}', test.name_en)
        level_name = getattr(test.level, f'name_{language}', test.level.name_en) if test.level else None
        
        test_list.append({
            "id": test.id,
            "name": test_name,
            "price": float(test.price),
            "level_id": test.level_id,
            "level_name": level_name,
            "subject_id": test.level.subject_id if test.level else None,
            "question_count": question_count
        })
    
    return {
        "items": test_list,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/tests/{test_id}", response_model=TestDetailResponse)
async def get_test_detail(
    test_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get a single test with all its questions and options.
    
    Args:
        test_id: Test ID
        
    Language is extracted from Accept-Language header (defaults to 'en').
        
    Returns:
        Test details including all questions with their options in requested language
        
    Raises:
        HTTPException: 404 if test not found
    """
    language = get_language_from_header(request)
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)
    
    # Get the test
    test = await test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Get test name in requested language
    test_name = getattr(test, f'name_{language}', test.name_en)
    level_name = getattr(test.level, f'name_{language}', test.level.name_en) if test.level else None
    
    # Get all questions for the test
    questions, _ = await question_repo.list_by_test(test_id, skip=0, limit=1000)
    
    # Build questions with options
    questions_detail = []
    for question in questions:
        # Get question text in requested language
        question_text = getattr(question, f'text_{language}', question.text_en)
        
        # Get all options for this question
        options = await option_repo.list_by_question(question.id)
        
        # Build options list
        options_detail = []
        for option in options:
            # Get option text in requested language
            option_text = getattr(option, f'text_{language}', option.text_en)
            options_detail.append(
                QuestionOptionResponse(
                    id=option.id,
                    label=option.label,
                    text=option_text
                )
            )
        
        questions_detail.append(
            QuestionDetailResponse(
                id=question.id,
                text=question_text,
                correct_answer=question.correct_answer,
                options=options_detail
            )
        )
    
    return TestDetailResponse(
        id=test.id,
        name=test_name,
        price=float(test.price),
        level_id=test.level_id,
        level_name=level_name,
        subject_id=test.level.subject_id if test.level else None,
        questions=questions_detail
    )




@router.post("/tests/{test_id}/submit-answers", response_model=SubmitAnswersResponse)
async def submit_answers(
    test_id: int,
    request_body: SubmitAnswersRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit answers for a test and get results.
    
    Args:
        test_id: Test ID
        request_body: JSON body with answers array
        
    Request body:
        {
            "answers": [
                {"question_id": 1, "answer": "A"},
                {"question_id": 2, "answer": "B"},
                ...
            ]
        }
        
    Returns:
        {
            "test_id": 1,
            "total_questions": 10,
            "correct_answers": 8,
            "score": 80,
            "results": [
                {
                    "question_id": 1,
                    "submitted_answer": "A",
                    "correct_answer": "A",
                    "is_correct": true
                },
                ...
            ]
        }
    """
    # Validate test exists
    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Create a map of question_id -> submitted_answer
    answer_map = {a.question_id: a.answer for a in request_body.answers}
    
    # Get all questions for the test
    question_repo = QuestionRepository(db)
    questions, _ = await question_repo.list_by_test(test_id, skip=0, limit=1000)
    
    # Build results
    results = []
    for question in questions:
        submitted_answer = answer_map.get(question.id, "")
        result = AnswerResult(
            question_id=question.id,
            submitted_answer=submitted_answer,
            correct_answer=question.correct_answer,
            is_correct=submitted_answer == question.correct_answer
        )
        results.append(result)
    
    # Calculate score
    total_questions = len(results)
    correct_answers = sum(1 for r in results if r.is_correct)
    score = int((correct_answers / total_questions * 100)) if total_questions > 0 else 0
    
    return SubmitAnswersResponse(
        test_id=test_id,
        total_questions=total_questions,
        correct_answers=correct_answers,
        score=score,
        results=results
    )
