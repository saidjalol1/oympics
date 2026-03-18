"""Subject service for business logic and validation.

This module provides the SubjectService class for managing subject operations,
including creation, retrieval, updates, and deletion with comprehensive validation.
"""

from typing import Tuple, List, Optional
from app.models.subject import Subject
from app.repositories.subject_repository import SubjectRepository
from app.services.translation_service import TranslationService
from app.core.exceptions import (
    ResourceNotFoundError,
    ResourceConflictError,
    ValidationError
)


class SubjectService:
    """Service for subject business logic and validation.
    
    Handles all subject operations including creation, retrieval, updates,
    and deletion with comprehensive validation and error handling.
    """
    
    def __init__(self, subject_repository: SubjectRepository, translation_service: TranslationService):
        """Initialize SubjectService with dependencies.
        
        Args:
            subject_repository: SubjectRepository instance for database operations
            translation_service: TranslationService instance for multi-language handling
        """
        self.subject_repo = subject_repository
        self.translation_service = translation_service
    
    async def create_subject(
        self,
        name_en: Optional[str] = None,
        name_uz: Optional[str] = None,
        name_ru: Optional[str] = None,
        name: Optional[str] = None
    ) -> Subject:
        """Create a new subject.
        
        Args:
            name_en: Subject name in English (optional if using legacy format)
            name_uz: Subject name in Uzbek (optional if using legacy format)
            name_ru: Subject name in Russian (optional if using legacy format)
            name: Legacy subject name (optional, for backward compatibility)
            
        Returns:
            Created Subject instance
            
        Raises:
            ValidationError: If translations are invalid
            ResourceConflictError: If subject with same name already exists
        """
        # Handle legacy input format
        if name and not (name_en or name_uz or name_ru):
            translations = self.translation_service.handle_legacy_input(name, "name")
            name_en = translations["name_en"]
            name_uz = translations["name_uz"]
            name_ru = translations["name_ru"]
        
        # Validate translations
        self.translation_service.validate_translations(
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            field_name="name"
        )
        
        # Validate individual field lengths
        for lang, value in [("en", name_en), ("uz", name_uz), ("ru", name_ru)]:
            if len(value) < 1 or len(value) > 100:
                raise ValidationError(f"Subject name_{lang} must be between 1 and 100 characters")
            if value.strip() != value:
                raise ValidationError(f"Subject name_{lang} cannot have leading or trailing whitespace")
        
        # Check for duplicate (check English name)
        existing = await self.subject_repo.get_by_name(name_en)
        if existing:
            raise ResourceConflictError(f"Subject with name '{name_en}' already exists")
        
        # Prepare legacy field
        legacy_name = self.translation_service.prepare_legacy_field(
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru
        )
        
        return await self.subject_repo.create(
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            name=legacy_name
        )
    
    async def get_subject(self, subject_id: int) -> Subject:
        """Retrieve a subject by ID.
        
        Args:
            subject_id: Subject ID to retrieve
            
        Returns:
            Subject instance
            
        Raises:
            ResourceNotFoundError: If subject not found
        """
        subject = await self.subject_repo.get_by_id(subject_id)
        if not subject:
            raise ResourceNotFoundError(f"Subject with id {subject_id} not found")
        
        return subject
    
    async def list_subjects(
        self, 
        skip: int = 0, 
        limit: int = 50,
        search: str = None
    ) -> Tuple[List[Subject], int]:
        """List all subjects with pagination and search.
        
        Args:
            skip: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 50)
            search: Optional search term to filter by name
            
        Returns:
            Tuple of (subjects, total_count)
        """
        return await self.subject_repo.list(skip=skip, limit=limit, search=search)
    
    async def update_subject(
        self,
        subject_id: int,
        name_en: Optional[str] = None,
        name_uz: Optional[str] = None,
        name_ru: Optional[str] = None,
        name: Optional[str] = None
    ) -> Subject:
        """Update a subject.
        
        Args:
            subject_id: Subject ID to update
            name_en: New subject name in English (optional if using legacy format)
            name_uz: New subject name in Uzbek (optional if using legacy format)
            name_ru: New subject name in Russian (optional if using legacy format)
            name: Legacy subject name (optional, for backward compatibility)
            
        Returns:
            Updated Subject instance
            
        Raises:
            ValidationError: If translations are invalid
            ResourceNotFoundError: If subject not found
            ResourceConflictError: If new name already exists
        """
        # Verify subject exists
        subject = await self.subject_repo.get_by_id(subject_id)
        if not subject:
            raise ResourceNotFoundError(f"Subject with id {subject_id} not found")
        
        # Handle legacy input format
        if name and not (name_en or name_uz or name_ru):
            translations = self.translation_service.handle_legacy_input(name, "name")
            name_en = translations["name_en"]
            name_uz = translations["name_uz"]
            name_ru = translations["name_ru"]
        
        # Validate translations
        self.translation_service.validate_translations(
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            field_name="name"
        )
        
        # Validate individual field lengths
        for lang, value in [("en", name_en), ("uz", name_uz), ("ru", name_ru)]:
            if len(value) < 1 or len(value) > 100:
                raise ValidationError(f"Subject name_{lang} must be between 1 and 100 characters")
            if value.strip() != value:
                raise ValidationError(f"Subject name_{lang} cannot have leading or trailing whitespace")
        
        # Check for duplicate if English name is different
        if subject.name_en != name_en:
            existing = await self.subject_repo.get_by_name(name_en)
            if existing:
                raise ResourceConflictError(f"Subject with name '{name_en}' already exists")
        
        # Prepare legacy field
        legacy_name = self.translation_service.prepare_legacy_field(
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru
        )
        
        return await self.subject_repo.update(
            subject_id,
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            name=legacy_name
        )
    
    async def delete_subject(self, subject_id: int) -> None:
        """Delete a subject.
        
        Args:
            subject_id: Subject ID to delete
            
        Raises:
            ResourceNotFoundError: If subject not found
        """
        subject = await self.subject_repo.get_by_id(subject_id)
        if not subject:
            raise ResourceNotFoundError(f"Subject with id {subject_id} not found")
        
        await self.subject_repo.delete(subject_id)
