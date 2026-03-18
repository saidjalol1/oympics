"""Test repository for database operations.

This module provides the TestRepository class for managing test data persistence,
implementing all database operations for the Test model.
"""

from typing import Optional, Tuple, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test import Test
from app.models.level import Level
from app.models.subject import Subject
from app.repositories.base import BaseRepository


class TestRepository(BaseRepository[Test]):
    """Repository for Test model database operations.
    
    Handles all database operations for test records including creation,
    retrieval, updates, and deletion. Uses async database operations
    for optimal performance.
    """
    
    __test__ = False  # Tell pytest this is not a test class
    
    def __init__(self, db: AsyncSession):
        """Initialize TestRepository with database session.
        
        Args:
            db: Async database session for operations
        """
        super().__init__(Test, db)
    
    async def create(
        self, 
        level_id: int, 
        name_en: str,
        name_uz: str,
        name_ru: str,
        name: Optional[str] = None,
        price: Decimal = Decimal("0.00"),
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Test:
        """Create a new test record.
        
        Args:
            level_id: ID of the parent level
            name_en: Test name in English
            name_uz: Test name in Uzbek
            name_ru: Test name in Russian
            name: Legacy test name (optional, for backward compatibility)
            price: Test price (default: 0.00)
            start_date: Optional start date for test availability
            end_date: Optional end date for test availability
            
        Returns:
            Created Test instance with all fields populated
            
        Raises:
            IntegrityError: If test with same name already exists for level
        """
        return await super().create(
            level_id=level_id,
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            name=name,
            price=price,
            start_date=start_date,
            end_date=end_date
        )
    
    async def get_by_id(self, id: int) -> Optional[Test]:
        """Retrieve test by ID with level and subject relationships.
        
        Args:
            id: Test's primary key ID
            
        Returns:
            Test instance if found, None otherwise
        """
        result = await self.db.execute(
            select(Test)
            .options(
                selectinload(Test.level).selectinload(Level.subject)
            )
            .where(Test.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, level_id: int, name_en: str) -> Optional[Test]:
        """Retrieve test by English name within a level.
        
        Args:
            level_id: ID of the parent level
            name_en: Test name in English to search for
            
        Returns:
            Test instance if found, None otherwise
        """
        result = await self.db.execute(
            select(Test).where(
                (Test.level_id == level_id) & (Test.name_en == name_en)
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_level(
        self, 
        level_id: int, 
        skip: int = 0, 
        limit: int = 50,
        search: str = None,
        min_price: float = None,
        max_price: float = None,
        start_date_from: str = None,
        start_date_to: str = None
    ) -> Tuple[List[Test], int]:
        """Fetch paginated tests for a level with optional search and filters.
        
        Retrieves a paginated list of tests for a specific level,
        ordered by created_at descending. Search term filters across
        all three language fields (name_en, name_uz, name_ru).
        
        Args:
            level_id: ID of the parent level
            skip: Number of records to skip for pagination (default: 0)
            limit: Maximum number of records to return (default: 50)
            search: Optional search term to filter by name (case-insensitive, searches all languages)
            min_price: Optional minimum price filter
            max_price: Optional maximum price filter
            start_date_from: Optional start date from filter (ISO format)
            start_date_to: Optional start date to filter (ISO format)
            
        Returns:
            Tuple of (tests, total_count) where tests is a list of Test instances
            and total_count is the total number of tests matching the search criteria
        """
        # Build base query
        query = select(Test).where(Test.level_id == level_id)
        count_query = select(func.count(Test.id)).where(Test.level_id == level_id)
        
        # Add search filter if provided (search across all 3 languages)
        if search:
            search_filter = or_(
                Test.name_en.ilike(f"%{search}%"),
                Test.name_uz.ilike(f"%{search}%"),
                Test.name_ru.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Add price filters
        if min_price is not None:
            query = query.where(Test.price >= min_price)
            count_query = count_query.where(Test.price >= min_price)
        
        if max_price is not None:
            query = query.where(Test.price <= max_price)
            count_query = count_query.where(Test.price <= max_price)
        
        # Add date filters
        if start_date_from:
            query = query.where(Test.start_date >= start_date_from)
            count_query = count_query.where(Test.start_date >= start_date_from)
        
        if start_date_to:
            query = query.where(Test.start_date <= start_date_to)
            count_query = count_query.where(Test.start_date <= start_date_to)
        
        # Get total count for level
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Get paginated results
        result = await self.db.execute(
            query
            .options(
                selectinload(Test.level).selectinload(Level.subject)
            )
            .order_by(Test.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        tests = list(result.scalars().all())
        
        return (tests, total_count)
    
    async def list_all(
        self, 
        skip: int = 0, 
        limit: int = 50,
        search: str = None,
        subject_id: int = None,
        min_price: float = None,
        max_price: float = None,
        start_date_from: str = None,
        start_date_to: str = None
    ) -> Tuple[List[Test], int]:
        """Fetch paginated tests across all levels with optional search and filters.
        
        Retrieves a paginated list of all tests, ordered by created_at descending.
        Search term filters across all three language fields (name_en, name_uz, name_ru).
        
        Args:
            skip: Number of records to skip for pagination (default: 0)
            limit: Maximum number of records to return (default: 50)
            search: Optional search term to filter by name (case-insensitive, searches all languages)
            subject_id: Optional subject ID to filter tests by subject
            min_price: Optional minimum price filter
            max_price: Optional maximum price filter
            start_date_from: Optional start date from filter (ISO format)
            start_date_to: Optional start date to filter (ISO format)
            
        Returns:
            Tuple of (tests, total_count) where tests is a list of Test instances
            and total_count is the total number of tests matching the search criteria
        """
        # Build base query
        query = select(Test)
        count_query = select(func.count(Test.id))
        
        # Add subject filter if provided (requires join with Level)
        if subject_id is not None:
            query = query.join(Level).where(Level.subject_id == subject_id)
            count_query = count_query.join(Level).where(Level.subject_id == subject_id)
        
        # Add search filter if provided (search across all 3 languages)
        if search:
            search_filter = or_(
                Test.name_en.ilike(f"%{search}%"),
                Test.name_uz.ilike(f"%{search}%"),
                Test.name_ru.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Add price filters
        if min_price is not None:
            query = query.where(Test.price >= min_price)
            count_query = count_query.where(Test.price >= min_price)
        
        if max_price is not None:
            query = query.where(Test.price <= max_price)
            count_query = count_query.where(Test.price <= max_price)
        
        # Add date filters
        if start_date_from:
            query = query.where(Test.start_date >= start_date_from)
            count_query = count_query.where(Test.start_date >= start_date_from)
        
        if start_date_to:
            query = query.where(Test.start_date <= start_date_to)
            count_query = count_query.where(Test.start_date <= start_date_to)
        
        # Get total count
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Get paginated results
        result = await self.db.execute(
            query
            .options(
                selectinload(Test.level).selectinload(Level.subject)
            )
            .order_by(Test.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        tests = list(result.scalars().all())
        
        return (tests, total_count)
    
    async def update(
        self, 
        id: int, 
        name_en: str,
        name_uz: str,
        name_ru: str,
        name: Optional[str] = None,
        price: Optional[Decimal] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Test:
        """Update test by ID.
        
        Args:
            id: Test's primary key ID
            name_en: New test name in English
            name_uz: New test name in Uzbek
            name_ru: New test name in Russian
            name: New legacy test name (optional)
            price: New test price (optional)
            start_date: New start date (or None to keep existing)
            end_date: New end date (or None to keep existing)
            
        Returns:
            Updated Test instance
            
        Raises:
            ValueError: If test with given ID does not exist
        """
        test = await self.get_by_id(id)
        if test is None:
            raise ValueError(f"Test with id {id} not found")
        
        return await super().update(
            test,
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            name=name,
            price=price,
            start_date=start_date,
            end_date=end_date
        )
    
    async def delete(self, id: int) -> None:
        """Delete test by ID.
        
        Args:
            id: Test's primary key ID
            
        Raises:
            ValueError: If test with given ID does not exist
        """
        test = await self.get_by_id(id)
        if test is None:
            raise ValueError(f"Test with id {id} not found")
        
        await super().delete(test)
