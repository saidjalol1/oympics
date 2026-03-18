"""Subject repository for database operations.

This module provides the SubjectRepository class for managing subject data persistence,
implementing all database operations for the Subject model.
"""

from typing import Optional, Tuple, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject
from app.repositories.base import BaseRepository


class SubjectRepository(BaseRepository[Subject]):
    """Repository for Subject model database operations.
    
    Handles all database operations for subject records including creation,
    retrieval, updates, and deletion. Uses async database operations
    for optimal performance.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize SubjectRepository with database session.
        
        Args:
            db: Async database session for operations
        """
        super().__init__(Subject, db)
    
    async def create(
        self,
        name_en: str,
        name_uz: str,
        name_ru: str,
        name: Optional[str] = None
    ) -> Subject:
        """Create a new subject record.
        
        Args:
            name_en: Subject name in English (must be unique)
            name_uz: Subject name in Uzbek
            name_ru: Subject name in Russian
            name: Legacy subject name (optional, for backward compatibility)
            
        Returns:
            Created Subject instance with all fields populated
            
        Raises:
            IntegrityError: If name_en already exists in database
        """
        return await super().create(
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            name=name
        )
    
    async def get_by_id(self, id: int) -> Optional[Subject]:
        """Retrieve subject by ID.
        
        Args:
            id: Subject's primary key ID
            
        Returns:
            Subject instance if found, None otherwise
        """
        return await super().get_by_id(id)
    
    async def get_by_name(self, name: str) -> Optional[Subject]:
        """Retrieve subject by English name.
        
        Args:
            name: Subject name in English to search for
            
        Returns:
            Subject instance if found, None otherwise
        """
        result = await self.db.execute(
            select(Subject).where(Subject.name_en == name)
        )
        return result.scalar_one_or_none()
    
    async def list(self, skip: int = 0, limit: int = 50, search: str = None) -> Tuple[List[Subject], int]:
        """Fetch paginated subjects with optional search.
        
        Retrieves a paginated list of subjects ordered by created_at descending.
        
        Args:
            skip: Number of records to skip for pagination (default: 0)
            limit: Maximum number of records to return (default: 50)
            search: Optional search term to filter by name (case-insensitive, searches all languages)
            
        Returns:
            Tuple of (subjects, total_count) where subjects is a list of Subject instances
            and total_count is the total number of subjects matching the search criteria
        """
        # Build base query
        query = select(Subject)
        count_query = select(func.count(Subject.id))
        
        # Add search filter if provided (search across all language fields)
        if search:
            search_filter = (
                Subject.name_en.ilike(f"%{search}%") |
                Subject.name_uz.ilike(f"%{search}%") |
                Subject.name_ru.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Get total count
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Get paginated results
        result = await self.db.execute(
            query
            .order_by(Subject.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        subjects = list(result.scalars().all())
        
        return (subjects, total_count)
    
    async def update(
        self,
        id: int,
        name_en: str,
        name_uz: str,
        name_ru: str,
        name: Optional[str] = None
    ) -> Subject:
        """Update subject by ID.
        
        Args:
            id: Subject's primary key ID
            name_en: New subject name in English
            name_uz: New subject name in Uzbek
            name_ru: New subject name in Russian
            name: Legacy subject name (optional, for backward compatibility)
            
        Returns:
            Updated Subject instance
            
        Raises:
            ValueError: If subject with given ID does not exist
        """
        subject = await self.get_by_id(id)
        if subject is None:
            raise ValueError(f"Subject with id {id} not found")
        
        return await super().update(
            subject,
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            name=name
        )
    
    async def delete(self, id: int) -> None:
        """Delete subject by ID.
        
        Args:
            id: Subject's primary key ID
            
        Raises:
            ValueError: If subject with given ID does not exist
        """
        subject = await self.get_by_id(id)
        if subject is None:
            raise ValueError(f"Subject with id {id} not found")
        
        await super().delete(subject)
