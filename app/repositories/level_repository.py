"""Level repository for database operations.

This module provides the LevelRepository class for managing level data persistence,
implementing all database operations for the Level model.
"""

from typing import Optional, Tuple, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.level import Level
from app.repositories.base import BaseRepository


class LevelRepository(BaseRepository[Level]):
    """Repository for Level model database operations.
    
    Handles all database operations for level records including creation,
    retrieval, updates, and deletion. Uses async database operations
    for optimal performance.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize LevelRepository with database session.
        
        Args:
            db: Async database session for operations
        """
        super().__init__(Level, db)
    
    async def create(
        self,
        subject_id: int,
        name_en: str,
        name_uz: str,
        name_ru: str,
        name: Optional[str] = None
    ) -> Level:
        """Create a new level record.
        
        Args:
            subject_id: ID of the parent subject
            name_en: Level name in English (must be unique within subject)
            name_uz: Level name in Uzbek
            name_ru: Level name in Russian
            name: Legacy level name (optional, for backward compatibility)
            
        Returns:
            Created Level instance with all fields populated
            
        Raises:
            IntegrityError: If level with same name_en already exists for subject
        """
        return await super().create(
            subject_id=subject_id,
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            name=name
        )
    
    async def get_by_id(self, id: int) -> Optional[Level]:
        """Retrieve level by ID.
        
        Args:
            id: Level's primary key ID
            
        Returns:
            Level instance if found, None otherwise
        """
        return await super().get_by_id(id)
    
    async def get_by_name(self, subject_id: int, name: str) -> Optional[Level]:
        """Retrieve level by English name within a subject.
        
        Args:
            subject_id: ID of the parent subject
            name: Level name in English to search for
            
        Returns:
            Level instance if found, None otherwise
        """
        result = await self.db.execute(
            select(Level).where(
                (Level.subject_id == subject_id) & (Level.name_en == name)
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_subject(
        self, 
        subject_id: int, 
        skip: int = 0, 
        limit: int = 50,
        search: str = None
    ) -> Tuple[List[Level], int]:
        """Fetch paginated levels for a subject with optional search.
        
        Retrieves a paginated list of levels for a specific subject,
        ordered by created_at descending.
        
        Args:
            subject_id: ID of the parent subject
            skip: Number of records to skip for pagination (default: 0)
            limit: Maximum number of records to return (default: 50)
            search: Optional search term to filter by name (case-insensitive, searches all languages)
            
        Returns:
            Tuple of (levels, total_count) where levels is a list of Level instances
            and total_count is the total number of levels matching the search criteria
        """
        # Build base query
        query = select(Level).where(Level.subject_id == subject_id)
        count_query = select(func.count(Level.id)).where(Level.subject_id == subject_id)
        
        # Add search filter if provided (search across all language fields)
        if search:
            search_filter = (
                Level.name_en.ilike(f"%{search}%") |
                Level.name_uz.ilike(f"%{search}%") |
                Level.name_ru.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Get total count for subject
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Get paginated results
        result = await self.db.execute(
            query
            .order_by(Level.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        levels = list(result.scalars().all())
        
        return (levels, total_count)
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 50,
        search: str = None
    ) -> Tuple[List[Level], int]:
        """Fetch paginated levels across all subjects with optional search.

        Retrieves a paginated list of levels from all subjects,
        ordered by created_at descending.

        Args:
            skip: Number of records to skip for pagination (default: 0)
            limit: Maximum number of records to return (default: 50)
            search: Optional search term to filter by name (case-insensitive, searches all languages)

        Returns:
            Tuple of (levels, total_count) where levels is a list of Level instances
            and total_count is the total number of levels matching the search criteria
        """
        # Build base query
        query = select(Level)
        count_query = select(func.count(Level.id))

        # Add search filter if provided (search across all language fields)
        if search:
            search_filter = (
                Level.name_en.ilike(f"%{search}%") |
                Level.name_uz.ilike(f"%{search}%") |
                Level.name_ru.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Get total count
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Get paginated results
        result = await self.db.execute(
            query
            .order_by(Level.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        levels = list(result.scalars().all())

        return (levels, total_count)

    
    async def update(
        self,
        id: int,
        name_en: str,
        name_uz: str,
        name_ru: str,
        name: Optional[str] = None,
        subject_id: Optional[int] = None
    ) -> Level:
        """Update level by ID.

        Args:
            id: Level's primary key ID
            name_en: New level name in English
            name_uz: New level name in Uzbek
            name_ru: New level name in Russian
            name: Legacy level name (optional, for backward compatibility)
            subject_id: New subject ID to move level to (optional)

        Returns:
            Updated Level instance

        Raises:
            ValueError: If level with given ID does not exist
        """
        level = await self.get_by_id(id)
        if level is None:
            raise ValueError(f"Level with id {id} not found")

        # Prepare update data
        update_data = {
            "name_en": name_en,
            "name_uz": name_uz,
            "name_ru": name_ru,
            "name": name
        }

        # Add subject_id if provided
        if subject_id is not None:
            update_data["subject_id"] = subject_id

        return await super().update(level, **update_data)
    
    async def delete(self, id: int) -> None:
        """Delete level by ID.
        
        Args:
            id: Level's primary key ID
            
        Raises:
            ValueError: If level with given ID does not exist
        """
        level = await self.get_by_id(id)
        if level is None:
            raise ValueError(f"Level with id {id} not found")
        
        await super().delete(level)
