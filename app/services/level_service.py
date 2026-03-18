"""Level service for business logic and validation.

This module provides the LevelService class for managing level operations,
including creation, retrieval, updates, and deletion with comprehensive validation.
"""

from typing import Tuple, List, Optional
from app.models.level import Level
from app.repositories.level_repository import LevelRepository
from app.repositories.subject_repository import SubjectRepository
from app.services.translation_service import TranslationService
from app.core.exceptions import (
    ResourceNotFoundError,
    ResourceConflictError,
    ValidationError
)


class LevelService:
    """Service for level business logic and validation.
    
    Handles all level operations including creation, retrieval, updates,
    and deletion with comprehensive validation and error handling.
    """
    
    def __init__(
        self, 
        level_repository: LevelRepository,
        subject_repository: SubjectRepository,
        translation_service: TranslationService
    ):
        """Initialize LevelService with dependencies.
        
        Args:
            level_repository: LevelRepository instance for database operations
            subject_repository: SubjectRepository instance for subject validation
            translation_service: TranslationService instance for multi-language handling
        """
        self.level_repo = level_repository
        self.subject_repo = subject_repository
        self.translation_service = translation_service
    
    async def create_level(
        self,
        subject_id: int,
        name_en: Optional[str] = None,
        name_uz: Optional[str] = None,
        name_ru: Optional[str] = None,
        name: Optional[str] = None
    ) -> Level:
        """Create a new level.
        
        Args:
            subject_id: Parent subject ID
            name_en: Level name in English (optional if using legacy format)
            name_uz: Level name in Uzbek (optional if using legacy format)
            name_ru: Level name in Russian (optional if using legacy format)
            name: Legacy level name (optional, for backward compatibility)
            
        Returns:
            Created Level instance
            
        Raises:
            ValidationError: If translations are invalid
            ResourceNotFoundError: If subject not found
            ResourceConflictError: If level with same name already exists in subject
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
                raise ValidationError(f"Level name_{lang} must be between 1 and 100 characters")
            if value.strip() != value:
                raise ValidationError(f"Level name_{lang} cannot have leading or trailing whitespace")
        
        # Check for duplicate within subject (check English name)
        existing = await self.level_repo.get_by_name(subject_id, name_en)
        if existing:
            raise ResourceConflictError(
                f"Level with name '{name_en}' already exists in subject {subject_id}"
            )
        
        # Prepare legacy field
        legacy_name = self.translation_service.prepare_legacy_field(
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru
        )
        
        return await self.level_repo.create(
            subject_id=subject_id,
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            name=legacy_name
        )
    
    async def get_level(self, level_id: int) -> Level:
        """Retrieve a level by ID.
        
        Args:
            level_id: Level ID to retrieve
            
        Returns:
            Level instance
            
        Raises:
            ResourceNotFoundError: If level not found
        """
        level = await self.level_repo.get_by_id(level_id)
        if not level:
            raise ResourceNotFoundError(f"Level with id {level_id} not found")
        
        return level
    
    async def list_levels(
        self, 
        subject_id: int,
        skip: int = 0, 
        limit: int = 50,
        search: str = None
    ) -> Tuple[List[Level], int]:
        """List levels for a subject with pagination and search.
        
        Args:
            subject_id: Parent subject ID
            skip: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 50)
            search: Optional search term to filter by name
            
        Returns:
            Tuple of (levels, total_count)
            
        Raises:
            ResourceNotFoundError: If subject not found
        """
        # Verify subject exists
        subject = await self.subject_repo.get_by_id(subject_id)
        if not subject:
            raise ResourceNotFoundError(f"Subject with id {subject_id} not found")
        
        return await self.level_repo.list_by_subject(
            subject_id=subject_id,
            skip=skip,
            limit=limit,
            search=search
        )
    async def list_all_levels(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None
    ) -> Tuple[List[Level], int]:
        """List all levels across all subjects with pagination and search.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            search: Optional search term

        Returns:
            Tuple of (levels, total_count)
        """
        return await self.level_repo.list_all(skip=skip, limit=limit, search=search)

    
    async def update_level(
        self,
        level_id: int,
        name_en: Optional[str] = None,
        name_uz: Optional[str] = None,
        name_ru: Optional[str] = None,
        name: Optional[str] = None,
        subject_id: Optional[int] = None
    ) -> Level:
        """Update a level.
        
        Args:
            level_id: Level ID to update
            name_en: New level name in English (optional if using legacy format)
            name_uz: New level name in Uzbek (optional if using legacy format)
            name_ru: New level name in Russian (optional if using legacy format)
            name: Legacy level name (optional, for backward compatibility)
            subject_id: New subject ID to move level to (optional)
            
        Returns:
            Updated Level instance
            
        Raises:
            ValidationError: If translations are invalid
            ResourceNotFoundError: If level not found or new subject not found
            ResourceConflictError: If new name already exists in subject
        """
        # Verify level exists
        level = await self.level_repo.get_by_id(level_id)
        if not level:
            raise ResourceNotFoundError(f"Level with id {level_id} not found")
        
        # Determine which subject to use for duplicate checking
        target_subject_id = subject_id if subject_id is not None else level.subject_id
        
        # Validate new subject exists if subject_id is provided
        if subject_id is not None:
            new_subject = await self.subject_repo.get_by_id(subject_id)
            if not new_subject:
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
                raise ValidationError(f"Level name_{lang} must be between 1 and 100 characters")
            if value.strip() != value:
                raise ValidationError(f"Level name_{lang} cannot have leading or trailing whitespace")
        
        # Check for duplicate if English name is different
        if level.name_en != name_en:
            existing = await self.level_repo.get_by_name(target_subject_id, name_en)
            if existing:
                raise ResourceConflictError(
                    f"Level with name '{name_en}' already exists in subject {target_subject_id}"
                )
        
        # Prepare legacy field
        legacy_name = self.translation_service.prepare_legacy_field(
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru
        )
        
        return await self.level_repo.update(
            level_id,
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            name=legacy_name,
            subject_id=subject_id
        )
    
    async def delete_level(self, level_id: int) -> None:
        """Delete a level.
        
        Args:
            level_id: Level ID to delete
            
        Raises:
            ResourceNotFoundError: If level not found
        """
        level = await self.level_repo.get_by_id(level_id)
        if not level:
            raise ResourceNotFoundError(f"Level with id {level_id} not found")
        
        await self.level_repo.delete(level_id)
