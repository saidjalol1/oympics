"""Test service for business logic and validation.

This module provides the TestService class for managing test operations,
including creation, retrieval, updates, and deletion with comprehensive validation.
"""

from typing import Tuple, List, Optional
from datetime import datetime
from decimal import Decimal
from app.models.test import Test
from app.repositories.test_repository import TestRepository
from app.repositories.level_repository import LevelRepository
from app.services.translation_service import TranslationService
from app.core.exceptions import (
    ResourceNotFoundError,
    ResourceConflictError,
    ValidationError
)


class TestService:
    """Service for test business logic and validation.
    
    Handles all test operations including creation, retrieval, updates,
    and deletion with comprehensive validation and error handling.
    """
    
    __test__ = False  # Tell pytest this is not a test class
    
    def __init__(
        self, 
        test_repository: TestRepository,
        level_repository: LevelRepository,
        translation_service: TranslationService
    ):
        """Initialize TestService with dependencies.
        
        Args:
            test_repository: TestRepository instance for database operations
            level_repository: LevelRepository instance for level validation
            translation_service: TranslationService instance for multi-language support
        """
        self.test_repo = test_repository
        self.level_repo = level_repository
        self.translation_service = translation_service
    
    def _validate_name(self, name: str) -> None:
        """Validate test name.
        
        Args:
            name: Test name to validate
            
        Raises:
            ValidationError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValidationError("Test name must be a non-empty string")
        
        if len(name) < 1 or len(name) > 100:
            raise ValidationError("Test name must be between 1 and 100 characters")
        
        if name.strip() != name:
            raise ValidationError("Test name cannot have leading or trailing whitespace")
    
    def _validate_price(self, price: Optional[float]) -> None:
        """Validate test price.
        
        Args:
            price: Test price to validate
            
        Raises:
            ValidationError: If price is invalid
        """
        if price is None:
            return
        
        if not isinstance(price, (int, float, Decimal)):
            raise ValidationError("Test price must be a number")
        
        if price < 0:
            raise ValidationError("Test price must be greater than or equal to 0")
        
        # Check for max 2 decimal places
        price_decimal = Decimal(str(price))
        if price_decimal.as_tuple().exponent < -2:
            raise ValidationError("Test price must have at most 2 decimal places")
    
    def _validate_dates(
        self, 
        start_date: Optional[datetime], 
        end_date: Optional[datetime]
    ) -> None:
        """Validate test dates.
        
        Args:
            start_date: Test start date
            end_date: Test end date
            
        Raises:
            ValidationError: If dates are invalid
        """
        if start_date is not None and not isinstance(start_date, datetime):
            raise ValidationError("start_date must be a datetime object")
        
        if end_date is not None and not isinstance(end_date, datetime):
            raise ValidationError("end_date must be a datetime object")
        
        if start_date is not None and end_date is not None:
            if end_date < start_date:
                raise ValidationError("end_date must be greater than or equal to start_date")
    
    async def create_test(
        self, 
        level_id: int, 
        name_en: Optional[str] = None,
        name_uz: Optional[str] = None,
        name_ru: Optional[str] = None,
        name: Optional[str] = None,
        price: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Test:
        """Create a new test.
        
        Args:
            level_id: Parent level ID
            name_en: Test name in English (optional if using legacy format)
            name_uz: Test name in Uzbek (optional if using legacy format)
            name_ru: Test name in Russian (optional if using legacy format)
            name: Legacy test name (optional, for backward compatibility)
            price: Test price (default: 0.00)
            start_date: Optional test start date
            end_date: Optional test end date
            
        Returns:
            Created Test instance
            
        Raises:
            ValidationError: If names, price, or dates are invalid
            ResourceNotFoundError: If level not found
            ResourceConflictError: If test with same name already exists in level
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
        
        # Validate each name field
        self._validate_name(name_en)
        self._validate_name(name_uz)
        self._validate_name(name_ru)
        
        # Validate price
        if price is None:
            price = 0.00
        self._validate_price(price)
        
        # Validate dates
        self._validate_dates(start_date, end_date)
        
        # Verify level exists
        level = await self.level_repo.get_by_id(level_id)
        if not level:
            raise ResourceNotFoundError(f"Level with id {level_id} not found")
        
        # Check for duplicate within level (check English name)
        existing = await self.test_repo.get_by_name(level_id, name_en)
        if existing:
            raise ResourceConflictError(
                f"Test with name '{name_en}' already exists in level {level_id}"
            )
        
        # Prepare legacy field
        legacy_name = self.translation_service.prepare_legacy_field(
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru
        )
        
        return await self.test_repo.create(
            level_id=level_id,
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            name=legacy_name,
            price=Decimal(str(price)),
            start_date=start_date,
            end_date=end_date
        )
    
    async def get_test(self, test_id: int) -> Test:
        """Retrieve a test by ID.
        
        Args:
            test_id: Test ID to retrieve
            
        Returns:
            Test instance
            
        Raises:
            ResourceNotFoundError: If test not found
        """
        test = await self.test_repo.get_by_id(test_id)
        if not test:
            raise ResourceNotFoundError(f"Test with id {test_id} not found")
        
        return test
    
    async def list_tests(
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
        """List tests for a level with pagination, search, and filters.
        
        Args:
            level_id: Parent level ID
            skip: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 50)
            search: Optional search term to filter by name (searches all languages)
            min_price: Optional minimum price filter
            max_price: Optional maximum price filter
            start_date_from: Optional start date from filter (ISO format)
            start_date_to: Optional start date to filter (ISO format)
            
        Returns:
            Tuple of (tests, total_count)
            
        Raises:
            ResourceNotFoundError: If level not found
        """
        # Verify level exists
        level = await self.level_repo.get_by_id(level_id)
        if not level:
            raise ResourceNotFoundError(f"Level with id {level_id} not found")
        
        return await self.test_repo.list_by_level(
            level_id=level_id,
            skip=skip,
            limit=limit,
            search=search,
            min_price=min_price,
            max_price=max_price,
            start_date_from=start_date_from,
            start_date_to=start_date_to
        )
    
    async def list_all_tests(
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
        """List all tests across all levels with pagination, search, and filters.
        
        Args:
            skip: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 50)
            search: Optional search term to filter by name (searches all languages)
            subject_id: Optional subject ID to filter tests by subject
            min_price: Optional minimum price filter
            max_price: Optional maximum price filter
            start_date_from: Optional start date from filter (ISO format)
            start_date_to: Optional start date to filter (ISO format)
            
        Returns:
            Tuple of (tests, total_count)
        """
        return await self.test_repo.list_all(
            skip=skip,
            limit=limit,
            search=search,
            subject_id=subject_id,
            min_price=min_price,
            max_price=max_price,
            start_date_from=start_date_from,
            start_date_to=start_date_to
        )
    
    async def update_test(
        self, 
        test_id: int, 
        name_en: Optional[str] = None,
        name_uz: Optional[str] = None,
        name_ru: Optional[str] = None,
        name: Optional[str] = None,
        price: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        level_id: Optional[int] = None
    ) -> Test:
        """Update a test.
        
        Args:
            test_id: Test ID to update
            name_en: New test name in English (optional if using legacy format)
            name_uz: New test name in Uzbek (optional if using legacy format)
            name_ru: New test name in Russian (optional if using legacy format)
            name: Legacy test name (optional, for backward compatibility)
            price: New test price (optional)
            start_date: New start date (optional)
            end_date: New end date (optional)
            level_id: New level ID (optional)
            
        Returns:
            Updated Test instance
            
        Raises:
            ValidationError: If names, price, or dates are invalid
            ResourceNotFoundError: If test or level not found
            ResourceConflictError: If new name already exists in level
        """
        # Verify test exists
        test = await self.test_repo.get_by_id(test_id)
        if not test:
            raise ResourceNotFoundError(f"Test with id {test_id} not found")
        
        # Handle legacy input format
        if name and not (name_en or name_uz or name_ru):
            translations = self.translation_service.handle_legacy_input(name, "name")
            name_en = translations["name_en"]
            name_uz = translations["name_uz"]
            name_ru = translations["name_ru"]
        
        # Use existing values if not provided
        if name_en is None:
            name_en = test.name_en
        if name_uz is None:
            name_uz = test.name_uz
        if name_ru is None:
            name_ru = test.name_ru
        if price is None:
            price = float(test.price)
        if level_id is None:
            level_id = test.level_id
        
        # Verify level exists if changing
        if level_id != test.level_id:
            level = await self.level_repo.get_by_id(level_id)
            if not level:
                raise ResourceNotFoundError(f"Level with id {level_id} not found")
        
        # Validate translations
        self.translation_service.validate_translations(
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            field_name="name"
        )
        
        # Validate each name field
        self._validate_name(name_en)
        self._validate_name(name_uz)
        self._validate_name(name_ru)
        
        # Validate price
        self._validate_price(price)
        
        # Validate dates
        self._validate_dates(start_date, end_date)
        
        # Check for duplicate if English name is different or level changed
        if test.name_en != name_en or test.level_id != level_id:
            existing = await self.test_repo.get_by_name(level_id, name_en)
            if existing and existing.id != test_id:
                raise ResourceConflictError(
                    f"Test with name '{name_en}' already exists in level {level_id}"
                )
        
        # Prepare legacy field
        legacy_name = self.translation_service.prepare_legacy_field(
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru
        )
        
        # Update level_id if changed
        if level_id != test.level_id:
            test.level_id = level_id
        
        return await self.test_repo.update(
            test_id,
            name_en=name_en,
            name_uz=name_uz,
            name_ru=name_ru,
            name=legacy_name,
            price=Decimal(str(price)),
            start_date=start_date,
            end_date=end_date
        )
    
    async def delete_test(self, test_id: int) -> None:
        """Delete a test.
        
        Args:
            test_id: Test ID to delete
            
        Raises:
            ResourceNotFoundError: If test not found
        """
        test = await self.test_repo.get_by_id(test_id)
        if not test:
            raise ResourceNotFoundError(f"Test with id {test_id} not found")
        
        await self.test_repo.delete(test_id)
