"""QuestionOption repository for database operations.

This module provides the QuestionOptionRepository class for managing question option data persistence,
implementing all database operations for the QuestionOption model.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question_option import QuestionOption
from app.repositories.base import BaseRepository


class QuestionOptionRepository(BaseRepository[QuestionOption]):
    """Repository for QuestionOption model database operations.
    
    Handles all database operations for question option records including creation,
    retrieval, updates, and deletion. Uses async database operations
    for optimal performance.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize QuestionOptionRepository with database session.
        
        Args:
            db: Async database session for operations
        """
        super().__init__(QuestionOption, db)
    
    async def create(
        self, 
        question_id: int, 
        label: str,
        text_en: str = None,
        text_uz: str = None,
        text_ru: str = None,
        text: str = None
    ) -> QuestionOption:
        """Create a new question option record.
        
        Args:
            question_id: ID of the parent question
            label: Option label (A, B, C, or D)
            text_en: Option text in English
            text_uz: Option text in Uzbek
            text_ru: Option text in Russian
            text: Legacy option text (for backward compatibility)
            
        Returns:
            Created QuestionOption instance with all fields populated
            
        Raises:
            IntegrityError: If option with same label already exists for question
        """
        return await super().create(
            question_id=question_id,
            label=label,
            text_en=text_en,
            text_uz=text_uz,
            text_ru=text_ru,
            text=text
        )
    
    async def get_by_id(self, id: int) -> Optional[QuestionOption]:
        """Retrieve question option by ID.
        
        Args:
            id: QuestionOption's primary key ID
            
        Returns:
            QuestionOption instance if found, None otherwise
        """
        return await super().get_by_id(id)
    
    async def list_by_question(self, question_id: int) -> List[QuestionOption]:
        """Fetch all options for a question.
        
        Retrieves all options for a specific question, ordered by label (A, B, C, D).
        
        Args:
            question_id: ID of the parent question
            
        Returns:
            List of QuestionOption instances for the question
        """
        result = await self.db.execute(
            select(QuestionOption)
            .where(QuestionOption.question_id == question_id)
            .order_by(QuestionOption.label.asc())
        )
        return list(result.scalars().all())
    
    async def update(
        self, 
        id: int, 
        label: str, 
        text: str
    ) -> QuestionOption:
        """Update question option by ID.
        
        Args:
            id: QuestionOption's primary key ID
            label: New option label (A, B, C, or D)
            text: New option text content
            
        Returns:
            Updated QuestionOption instance
            
        Raises:
            ValueError: If question option with given ID does not exist
        """
        option = await self.get_by_id(id)
        if option is None:
            raise ValueError(f"QuestionOption with id {id} not found")
        
        return await super().update(
            option,
            label=label,
            text=text
        )
    
    async def delete(self, id: int) -> None:
        """Delete question option by ID.
        
        Args:
            id: QuestionOption's primary key ID
            
        Raises:
            ValueError: If question option with given ID does not exist
        """
        option = await self.get_by_id(id)
        if option is None:
            raise ValueError(f"QuestionOption with id {id} not found")
        
        await super().delete(option)
