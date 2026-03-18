"""Image repository for question image database operations.

This module provides the ImageRepository class for managing QuestionImage
database operations including CRUD operations and queries.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question_image import QuestionImage
from app.repositories.base import BaseRepository


class ImageRepository(BaseRepository[QuestionImage]):
    """Repository for QuestionImage database operations.
    
    Provides methods for creating, reading, updating, and deleting question images,
    as well as specialized queries for image management.
    
    Attributes:
        model: QuestionImage model class
        db: Async database session
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with QuestionImage model and database session.
        
        Args:
            db: Async database session for operations
        """
        super().__init__(QuestionImage, db)
    
    async def get_by_question_id(self, question_id: int) -> List[QuestionImage]:
        """Retrieve all images for a specific question.
        
        Args:
            question_id: Question ID to retrieve images for
            
        Returns:
            List of QuestionImage instances ordered by image_order
        """
        result = await self.db.execute(
            select(QuestionImage)
            .where(QuestionImage.question_id == question_id)
            .order_by(QuestionImage.image_order)
        )
        return list(result.scalars().all())
    
    async def get_by_question_and_order(
        self, 
        question_id: int, 
        image_order: int
    ) -> Optional[QuestionImage]:
        """Retrieve a specific image by question ID and order.
        
        Args:
            question_id: Question ID
            image_order: Image order (1 or 2)
            
        Returns:
            QuestionImage instance if found, None otherwise
        """
        result = await self.db.execute(
            select(QuestionImage)
            .where(
                QuestionImage.question_id == question_id,
                QuestionImage.image_order == image_order
            )
        )
        return result.scalar_one_or_none()
    
    async def count_by_question_id(self, question_id: int) -> int:
        """Count the number of images for a specific question.
        
        Args:
            question_id: Question ID to count images for
            
        Returns:
            Number of images attached to the question
        """
        images = await self.get_by_question_id(question_id)
        return len(images)
    
    async def delete_by_question_id(self, question_id: int) -> None:
        """Delete all images for a specific question.
        
        Args:
            question_id: Question ID to delete images for
        """
        images = await self.get_by_question_id(question_id)
        for image in images:
            await self.delete(image)
