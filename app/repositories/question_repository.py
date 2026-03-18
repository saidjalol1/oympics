"""Question repository for database operations.

This module provides the QuestionRepository class for managing question data persistence,
implementing all database operations for the Question model.
"""

from typing import Optional, Tuple, List
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.repositories.base import BaseRepository


class QuestionRepository(BaseRepository[Question]):
    """Repository for Question model database operations.
    
    Handles all database operations for question records including creation,
    retrieval, updates, and deletion. Uses async database operations
    for optimal performance.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize QuestionRepository with database session.
        
        Args:
            db: Async database session for operations
        """
        super().__init__(Question, db)
    
    async def create(
        self, 
        test_id: int, 
        text_en: str,
        text_uz: str,
        text_ru: str,
        text: str,
        correct_answer: str
    ) -> Question:
        """Create a new question record.
        
        Args:
            test_id: ID of the parent test
            text_en: Question text in English
            text_uz: Question text in Uzbek
            text_ru: Question text in Russian
            text: Legacy question text (for backward compatibility)
            correct_answer: Correct answer label (A, B, C, or D)
            
        Returns:
            Created Question instance with all fields populated
        """
        return await super().create(
            test_id=test_id,
            text_en=text_en,
            text_uz=text_uz,
            text_ru=text_ru,
            text=text,
            correct_answer=correct_answer
        )
    
    async def get_by_id(self, id: int) -> Optional[Question]:
        """Retrieve question by ID with images relationship.
        
        Args:
            id: Question's primary key ID
            
        Returns:
            Question instance if found, None otherwise
        """
        result = await self.db.execute(
            select(Question)
            .where(Question.id == id)
            .options(
                selectinload(Question.options),
                selectinload(Question.images)
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_test(
        self, 
        test_id: int, 
        skip: int = 0, 
        limit: int = 100,
        search: str = None
    ) -> Tuple[List[Question], int]:
        """Fetch paginated questions for a test with optional search.
        
        Retrieves a paginated list of questions for a specific test,
        ordered by created_at ascending (in order of creation).
        Searches across all 3 language fields.
        
        Args:
            test_id: ID of the parent test
            skip: Number of records to skip for pagination (default: 0)
            limit: Maximum number of records to return (default: 100)
            search: Optional search term to filter by question text (case-insensitive, searches all languages)
            
        Returns:
            Tuple of (questions, total_count) where questions is a list of Question instances
            and total_count is the total number of questions matching the search criteria
        """
        # Build base query
        query = select(Question).where(Question.test_id == test_id)
        count_query = select(func.count(Question.id)).where(Question.test_id == test_id)
        
        # Add search filter if provided - search across all 3 language fields
        if search:
            search_filter = (
                Question.text_en.ilike(f"%{search}%") |
                Question.text_uz.ilike(f"%{search}%") |
                Question.text_ru.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Get total count for test
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Get paginated results with eagerly loaded options and images
        result = await self.db.execute(
            query
            .order_by(Question.created_at.asc())
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(Question.options),
                selectinload(Question.images)
            )
        )
        questions = list(result.scalars().all())
        
        return (questions, total_count)
    
    async def update(
        self, 
        id: int, 
        text_en: str,
        text_uz: str,
        text_ru: str,
        text: str,
        correct_answer: str
    ) -> Question:
        """Update question by ID.
        
        Args:
            id: Question's primary key ID
            text_en: New question text in English
            text_uz: New question text in Uzbek
            text_ru: New question text in Russian
            text: New legacy question text (for backward compatibility)
            correct_answer: New correct answer label (A, B, C, or D)
            
        Returns:
            Updated Question instance
            
        Raises:
            ValueError: If question with given ID does not exist
        """
        question = await self.get_by_id(id)
        if question is None:
            raise ValueError(f"Question with id {id} not found")
        
        return await super().update(
            question,
            text_en=text_en,
            text_uz=text_uz,
            text_ru=text_ru,
            text=text,
            correct_answer=correct_answer
        )
    
    async def delete(self, id: int) -> None:
        """Delete question by ID.
        
        Args:
            id: Question's primary key ID
            
        Raises:
            ValueError: If question with given ID does not exist
        """
        question = await self.get_by_id(id)
        if question is None:
            raise ValueError(f"Question with id {id} not found")
        
        await super().delete(question)
