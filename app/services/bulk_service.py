"""Bulk operations service for batch delete operations.

This module provides the BulkService class for handling bulk delete operations
on subjects, levels, tests, and questions with transaction support and atomicity.
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.repositories.subject_repository import SubjectRepository
from app.repositories.level_repository import LevelRepository
from app.repositories.test_repository import TestRepository
from app.repositories.question_repository import QuestionRepository
from app.services.image_service import ImageService


class BulkService:
    """Service for bulk operations with transaction support.
    
    Provides methods for bulk delete operations on subjects, levels, tests,
    and questions. All operations are atomic - either all items are deleted
    or none are deleted (rollback on failure).
    
    Attributes:
        db: AsyncSession for database operations
        subject_repo: SubjectRepository instance
        level_repo: LevelRepository instance
        test_repo: TestRepository instance
        question_repo: QuestionRepository instance
        image_service: ImageService instance for image cleanup
    """
    
    def __init__(
        self,
        db: AsyncSession,
        subject_repo: SubjectRepository,
        level_repo: LevelRepository,
        test_repo: TestRepository,
        question_repo: QuestionRepository,
        image_service: ImageService
    ):
        """Initialize BulkService with dependencies.
        
        Args:
            db: AsyncSession for transaction management
            subject_repo: SubjectRepository instance
            level_repo: LevelRepository instance
            test_repo: TestRepository instance
            question_repo: QuestionRepository instance
            image_service: ImageService instance for image cleanup
        """
        self.db = db
        self.subject_repo = subject_repo
        self.level_repo = level_repo
        self.test_repo = test_repo
        self.question_repo = question_repo
        self.image_service = image_service
    
    async def bulk_delete_subjects(self, subject_ids: List[int]) -> None:
        """Delete multiple subjects atomically.
        
        Deletes all specified subjects in a single transaction. If any deletion
        fails, all changes are rolled back. Cascade deletion handles:
        - Subjects → Levels → Tests → Questions → Images
        
        Args:
            subject_ids: List of subject IDs to delete
            
        Raises:
            ValidationError: If subject_ids list is empty
            ResourceNotFoundError: If any subject ID doesn't exist
            
        Examples:
            >>> service = BulkService(db, repos...)
            >>> await service.bulk_delete_subjects([1, 2, 3])
        """
        # Validate input
        if not subject_ids:
            raise ValidationError("Subject IDs list cannot be empty")
        
        # Validate all subjects exist
        for subject_id in subject_ids:
            subject = await self.subject_repo.get_by_id(subject_id)
            if not subject:
                raise ResourceNotFoundError(
                    f"Subject with id {subject_id} not found"
                )
        
        # Delete all subjects (cascade will handle related entities)
        try:
            for subject_id in subject_ids:
                await self.subject_repo.delete(subject_id)
            
            # Commit is handled by the dependency injection layer
        except Exception as e:
            # Rollback is handled by the dependency injection layer
            raise ValidationError(f"Failed to delete subjects: {str(e)}")
    
    async def bulk_delete_levels(self, level_ids: List[int]) -> None:
        """Delete multiple levels atomically.
        
        Deletes all specified levels in a single transaction. If any deletion
        fails, all changes are rolled back. Cascade deletion handles:
        - Levels → Tests → Questions → Images
        
        Args:
            level_ids: List of level IDs to delete
            
        Raises:
            ValidationError: If level_ids list is empty
            ResourceNotFoundError: If any level ID doesn't exist
            
        Examples:
            >>> service = BulkService(db, repos...)
            >>> await service.bulk_delete_levels([1, 2, 3])
        """
        # Validate input
        if not level_ids:
            raise ValidationError("Level IDs list cannot be empty")
        
        # Validate all levels exist
        for level_id in level_ids:
            level = await self.level_repo.get_by_id(level_id)
            if not level:
                raise ResourceNotFoundError(
                    f"Level with id {level_id} not found"
                )
        
        # Delete all levels (cascade will handle related entities)
        try:
            for level_id in level_ids:
                await self.level_repo.delete(level_id)
            
            # Commit is handled by the dependency injection layer
        except Exception as e:
            # Rollback is handled by the dependency injection layer
            raise ValidationError(f"Failed to delete levels: {str(e)}")
    
    async def bulk_delete_tests(self, test_ids: List[int]) -> None:
        """Delete multiple tests atomically.
        
        Deletes all specified tests in a single transaction. If any deletion
        fails, all changes are rolled back. Cascade deletion handles:
        - Tests → Questions → Images
        
        Args:
            test_ids: List of test IDs to delete
            
        Raises:
            ValidationError: If test_ids list is empty
            ResourceNotFoundError: If any test ID doesn't exist
            
        Examples:
            >>> service = BulkService(db, repos...)
            >>> await service.bulk_delete_tests([1, 2, 3])
        """
        # Validate input
        if not test_ids:
            raise ValidationError("Test IDs list cannot be empty")
        
        # Validate all tests exist
        for test_id in test_ids:
            test = await self.test_repo.get_by_id(test_id)
            if not test:
                raise ResourceNotFoundError(
                    f"Test with id {test_id} not found"
                )
        
        # Delete all tests (cascade will handle related entities)
        try:
            for test_id in test_ids:
                await self.test_repo.delete(test_id)
            
            # Commit is handled by the dependency injection layer
        except Exception as e:
            # Rollback is handled by the dependency injection layer
            raise ValidationError(f"Failed to delete tests: {str(e)}")
    
    async def bulk_delete_questions(self, question_ids: List[int]) -> None:
        """Delete multiple questions atomically with image cleanup.
        
        Deletes all specified questions in a single transaction. If any deletion
        fails, all changes are rolled back. Before deleting questions, cleans up
        associated images from the filesystem. Cascade deletion handles:
        - Questions → Options, Images
        
        Args:
            question_ids: List of question IDs to delete
            
        Raises:
            ValidationError: If question_ids list is empty
            ResourceNotFoundError: If any question ID doesn't exist
            
        Examples:
            >>> service = BulkService(db, repos...)
            >>> await service.bulk_delete_questions([1, 2, 3])
        """
        # Validate input
        if not question_ids:
            raise ValidationError("Question IDs list cannot be empty")
        
        # Validate all questions exist
        for question_id in question_ids:
            question = await self.question_repo.get_by_id(question_id)
            if not question:
                raise ResourceNotFoundError(
                    f"Question with id {question_id} not found"
                )
        
        # Delete images for all questions first
        try:
            for question_id in question_ids:
                await self.image_service.delete_question_images(question_id)
        except Exception as e:
            raise ValidationError(f"Failed to delete question images: {str(e)}")
        
        # Delete all questions (cascade will handle options)
        try:
            for question_id in question_ids:
                await self.question_repo.delete(question_id)
            
            # Commit is handled by the dependency injection layer
        except Exception as e:
            # Rollback is handled by the dependency injection layer
            raise ValidationError(f"Failed to delete questions: {str(e)}")
