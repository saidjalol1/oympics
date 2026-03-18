"""Base repository class for database operations.

This module provides a base repository class with common database operation patterns
and async session management for all repository implementations.
"""

from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

# Type variable for model classes
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository class with common database operations.
    
    This class provides a foundation for all repository implementations,
    handling async session management and common CRUD operations.
    
    Attributes:
        model: The SQLAlchemy model class this repository manages
        db: The async database session
        
    Requirements:
        - 11.1: Repository handles all database operations
        - 11.3: Repository uses asynchronous database operations
    """
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """Initialize repository with model and database session.
        
        Args:
            model: SQLAlchemy model class to manage
            db: Async database session for operations
        """
        self.model = model
        self.db = db
    
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Retrieve a record by its primary key ID.
        
        Args:
            id: Primary key value to search for
            
        Returns:
            Model instance if found, None otherwise
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Retrieve all records with pagination.
        
        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
        """
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> ModelType:
        """Create a new record.
        
        Args:
            **kwargs: Field values for the new record
            
        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance
    
    async def update(self, instance: ModelType, **kwargs) -> ModelType:
        """Update an existing record.
        
        Args:
            instance: Model instance to update
            **kwargs: Field values to update
            
        Returns:
            Updated model instance
        """
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        await self.db.flush()
        await self.db.refresh(instance)
        return instance
    
    async def delete(self, instance: ModelType) -> None:
        """Delete a record.
        
        Args:
            instance: Model instance to delete
        """
        await self.db.delete(instance)
        await self.db.flush()
    
    async def exists(self, **filters) -> bool:
        """Check if a record exists matching the given filters.
        
        Args:
            **filters: Field name and value pairs to filter by
            
        Returns:
            True if at least one matching record exists, False otherwise
        """
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
