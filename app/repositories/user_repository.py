"""User repository for database operations.

This module provides the UserRepository class for managing user data persistence,
implementing all database operations for the User model.
"""

from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model database operations.
    
    Handles all database operations for user records including creation,
    retrieval, updates, and existence checks. Uses async database operations
    for optimal performance.
    
    Requirements:
        - 11.1: Repository handles all database operations for user data
        - 11.2: Repository provides methods for creating, reading, updating user records
        - 11.3: Repository uses asynchronous database operations
        - 11.5: Repository does not contain business logic
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize UserRepository with database session.
        
        Args:
            db: Async database session for operations
        """
        super().__init__(User, db)
    
    async def create(
        self, 
        email: str, 
        hashed_password: str, 
        is_verified: bool = False,
        is_admin: bool = False
    ) -> User:
        """Create a new user record.
        
        Args:
            email: User's email address (must be unique)
            hashed_password: Bcrypt hash of user's password
            is_verified: Whether user has verified their email (default: False)
            is_admin: Whether user has admin privileges (default: False)
            
        Returns:
            Created User instance with all fields populated
            
        Raises:
            IntegrityError: If email already exists in database
        """
        return await super().create(
            email=email,
            hashed_password=hashed_password,
            is_verified=is_verified,
            is_admin=is_admin
        )
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User instance if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve user by ID.
        
        Args:
            user_id: User's primary key ID
            
        Returns:
            User instance if found, None otherwise
        """
        return await super().get_by_id(user_id)
    
    async def update_verification_status(
        self, 
        user_id: int, 
        is_verified: bool
    ) -> User:
        """Update user's email verification status.
        
        Args:
            user_id: User's primary key ID
            is_verified: New verification status (True for verified, False for pending)
            
        Returns:
            Updated User instance
            
        Raises:
            ValueError: If user with given ID does not exist
        """
        user = await self.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User with id {user_id} not found")
        
        return await super().update(user, is_verified=is_verified)
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user with given email exists.
        
        Args:
            email: Email address to check
            
        Returns:
            True if user with email exists, False otherwise
        """
        return await super().exists(email=email)
    
    async def get_all_paginated(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        verified_only: Optional[bool] = None,
        is_admin: Optional[bool] = None
    ) -> tuple[list[User], int]:
        """Fetch paginated users with optional filters.
        
        Retrieves a paginated list of users with optional email search,
        verification status filtering, and admin status filtering. Results are 
        ordered by created_at descending (newest first).
        
        Preconditions:
            - skip >= 0 (non-negative offset)
            - limit > 0 and limit <= 100 (reasonable page size)
            - Database connection is active and valid
            
        Postconditions:
            - Returns tuple (users, total_count) where:
              - len(users) <= limit
              - total_count >= len(users)
              - total_count represents all matching users (not just current page)
            - Users are ordered by created_at DESC (newest first)
            - No passwords are included in response
            - If search provided, all returned users have email matching pattern
            - If verified_only provided, all returned users match verification status
            - If is_admin provided, all returned users match admin status
        
        Args:
            skip: Number of records to skip for pagination (default: 0)
            limit: Maximum number of records to return (default: 50, max: 100)
            search: Optional email search pattern for partial match (case-insensitive)
            verified_only: Optional filter by verification status (True/False/None)
            is_admin: Optional filter by admin status (True/False/None)
            
        Returns:
            Tuple of (users, total_count) where users is a list of User instances
            and total_count is the total number of matching users in database
            
        Raises:
            None - returns empty list if no matches found
        """
        # Build base query for filtering
        query = select(User)
        count_query = select(func.count(User.id))
        
        # Apply search filter if provided and not empty
        if search is not None and len(search) > 0:
            search_pattern = f"%{search}%"
            query = query.where(User.email.ilike(search_pattern))
            count_query = count_query.where(User.email.ilike(search_pattern))
        
        # Apply verification status filter if provided
        if verified_only is not None:
            query = query.where(User.is_verified == verified_only)
            count_query = count_query.where(User.is_verified == verified_only)
        
        # Apply admin status filter if provided
        if is_admin is not None:
            query = query.where(User.is_admin == is_admin)
            count_query = count_query.where(User.is_admin == is_admin)
        
        # Get total count of matching records
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar() or 0
        
        # Apply ordering and pagination
        query = query.order_by(User.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        # Execute query and get results
        result = await self.db.execute(query)
        users = list(result.scalars().all())
        
        return (users, total_count)
    
    async def update(
        self,
        user: User,
        **kwargs
    ) -> User:
        """Update user with provided fields.
        
        Updates a user record with the specified fields while preserving
        all fields not included in kwargs. Automatically refreshes the
        updated_at timestamp.
        
        Preconditions:
            - user is a valid User instance from database
            - user exists in database
            - kwargs contains only valid User field names
            - If 'email' in kwargs, it must be valid format and not taken
            - If 'hashed_password' in kwargs, it must be a valid bcrypt hash
            
        Postconditions:
            - Only specified fields in kwargs are updated
            - Unspecified fields retain their original values
            - updated_at timestamp is automatically refreshed
            - Returns updated User instance
            - Changes are persisted to database
            
        Args:
            user: User instance to update
            **kwargs: Fields to update (email, hashed_password, is_verified, is_admin)
            
        Returns:
            Updated User instance with all fields current
            
        Raises:
            None - relies on caller to validate field values
        """
        return await super().update(user, **kwargs)
    
    async def delete(self, user_id: int) -> None:
        """Delete user by ID.
        
        Removes a user record from the database by their primary key ID.
        This is a permanent deletion (no soft delete).
        
        Preconditions:
            - user_id > 0 (positive integer)
            - user_id exists in database
            - Database connection is active
            
        Postconditions:
            - User record is removed from database
            - No return value (void function)
            - Operation is irreversible
            
        Args:
            user_id: User's primary key ID to delete
            
        Raises:
            ValueError: If user with given ID does not exist
        """
        user = await self.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User with id {user_id} not found")
        
        await super().delete(user)
    
    async def count_all(
        self,
        search: Optional[str] = None,
        verified_only: Optional[bool] = None
    ) -> int:
        """Count users matching filters.
        
        Returns the total count of users matching the provided search and
        filter criteria. Uses the same filtering logic as get_all_paginated()
        to ensure consistency.
        
        Preconditions:
            - Database connection is active and valid
            - search parameter is optional (None or string)
            - verified_only parameter is optional (None, True, or False)
            
        Postconditions:
            - Returns accurate count of matching users
            - Count matches the total_count from get_all_paginated() with same filters
            - Returns 0 if no matches found
            
        Args:
            search: Optional email search pattern for partial match (case-insensitive)
            verified_only: Optional filter by verification status (True/False/None)
            
        Returns:
            Total count of users matching the filters
        """
        # Build count query
        query = select(func.count(User.id))
        
        # Apply search filter if provided and not empty
        if search is not None and len(search) > 0:
            search_pattern = f"%{search}%"
            query = query.where(User.email.ilike(search_pattern))
        
        # Apply verification status filter if provided
        if verified_only is not None:
            query = query.where(User.is_verified == verified_only)
        
        # Execute query and return count
        result = await self.db.execute(query)
        count = result.scalar() or 0
        
        return count
