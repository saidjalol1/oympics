"""Admin service layer for user management operations.

This module provides the AdminService class which orchestrates admin-specific
business logic for user management including CRUD operations, pagination,
filtering, and verification status management.
"""

from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.password_service import PasswordService
from app.exceptions import (
    ResourceNotFoundError,
    EmailAlreadyExistsError,
    AuthorizationError
)


class AdminService:
    """Service for admin panel operations.
    
    Orchestrates business logic for admin user management including:
    - Retrieving paginated user lists with filtering
    - Creating new users with admin bypass of email verification
    - Updating user details with partial field updates
    - Deleting user accounts with self-deletion prevention
    - Managing user verification status
    
    Requirements:
        - 2.1: Retrieve paginated user lists
        - 2.2: Support pagination with skip/limit
        - 2.3: Support email search filtering
        - 4.1: Create users with admin bypass
        - 5.1: Retrieve single user details
        - 6.1: Update user details with partial updates
        - 7.1: Delete user accounts
        - 8.1: Toggle verification status
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        password_service: PasswordService
    ):
        """Initialize AdminService with dependencies.
        
        Args:
            user_repository: UserRepository instance for database operations
            password_service: PasswordService instance for password hashing
        """
        self.user_repo = user_repository
        self.password_service = password_service
    
    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        verified_only: Optional[bool] = None,
        is_admin: Optional[bool] = None
    ) -> tuple[list[User], int]:
        """Retrieve paginated list of users with optional filtering.
        
        Fetches users from the database with pagination support and optional
        filtering by email search pattern, verification status, and admin status.
        Results are ordered by created_at in descending order (newest first).
        
        Args:
            skip: Number of records to skip for pagination (default: 0)
            limit: Maximum number of records to return (default: 50, max: 100)
            search: Optional email search filter (case-insensitive partial match)
            verified_only: Optional filter for verification status
                - True: return only verified users
                - False: return only unverified users
                - None: return all users regardless of verification status
            is_admin: Optional filter for admin status
                - True: return only admin users
                - False: return only non-admin users
                - None: return all users regardless of admin status
            
        Returns:
            Tuple of (user_list, total_count) where:
            - user_list: List of User objects for the current page
            - total_count: Total count of all users matching the filters
            
        Preconditions:
            - skip >= 0
            - limit > 0 and limit <= 100
            - Database connection is active
            
        Postconditions:
            - len(user_list) <= limit
            - total_count >= len(user_list)
            - Users ordered by created_at DESC (newest first)
            - No passwords included in response
            
        Requirements:
            - 2.1: Return paginated users
            - 2.2: Support skip/limit pagination
            - 2.3: Support email search filtering
            - 2.6: Order by created_at DESC
            - 2.9: Return accurate total count
            - 3.1: Support email search (case-insensitive)
            - 3.2: Support verified_only=true filter
            - 3.3: Support verified_only=false filter
            - 3.4: Apply search and filter with AND logic
            - 3.5: Treat empty search string as no filter
        """
        db = self.user_repo.db
        
        # Build base query
        query = select(User)
        count_query = select(func.count(User.id))
        
        # Apply search filter if provided and not empty
        if search is not None and len(search.strip()) > 0:
            search_pattern = f"%{search}%"
            query = query.where(User.email.ilike(search_pattern))
            count_query = count_query.where(User.email.ilike(search_pattern))
        
        # Apply verification filter if provided
        if verified_only is not None:
            query = query.where(User.is_verified == verified_only)
            count_query = count_query.where(User.is_verified == verified_only)
        
        # Apply admin status filter if provided
        if is_admin is not None:
            query = query.where(User.is_admin == is_admin)
            count_query = count_query.where(User.is_admin == is_admin)
        
        # Get total count matching filters
        total_result = await db.execute(count_query)
        total_count = total_result.scalar() or 0
        
        # Apply ordering and pagination
        query = query.order_by(User.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        users = list(result.scalars().all())
        
        return (users, total_count)
    
    async def get_user_by_id(self, user_id: int) -> User:
        """Retrieve single user by ID.
        
        Fetches a user record from the database by their primary key ID.
        
        Args:
            user_id: User's primary key ID
            
        Returns:
            User object with all fields populated
            
        Raises:
            ResourceNotFoundError: If user with given ID doesn't exist
            
        Preconditions:
            - user_id > 0
            - Database connection is active
            
        Postconditions:
            - Returns User object if found
            - Raises ResourceNotFoundError if not found
            
        Requirements:
            - 5.1: Retrieve user by ID
            - 5.2: Return 404 if user not found
            - 5.3: Include all user fields in response
            - 5.4: Never include hashed_password in response
        """
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ResourceNotFoundError(f"User {user_id} not found")
        return user
    
    async def create_user(
        self,
        email: str,
        password: str,
        is_verified: bool = False,
        is_admin: bool = False
    ) -> User:
        """Create new user account (admin bypass of email verification).
        
        Creates a new user record with the provided email and password.
        The password is hashed using bcrypt before storage. Admins can
        bypass email verification by setting is_verified=True and can
        grant admin privileges by setting is_admin=True.
        
        Args:
            email: User's email address (must be unique)
            password: Plain text password (will be hashed, must be 8-100 chars)
            is_verified: Initial verification status (default: False)
            is_admin: Whether to grant admin privileges (default: False)
            
        Returns:
            Created User object with all fields populated
            
        Raises:
            EmailAlreadyExistsError: If email already exists in database
            
        Preconditions:
            - email is valid email format
            - len(password) >= 8
            - email does not exist in database
            - Database connection is active
            
        Postconditions:
            - User created with hashed password
            - user.hashed_password != password (password is hashed)
            - user.is_verified matches input parameter
            - user.is_admin matches input parameter
            - user.created_at and updated_at set to current timestamp
            - User persisted in database
            
        Requirements:
            - 4.1: Create user via admin endpoint
            - 4.2: Hash password using bcrypt
            - 4.3: Never store plain text password
            - 4.4: Support is_verified=true for admin bypass
            - 4.5: Support is_verified=false for pending verification
            - 4.6: Set created_at and updated_at timestamps
            - 4.7: Reject duplicate email with 409 Conflict
            - 4.11: Return created user object
            - 12.1: Enforce email uniqueness
        """
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user is not None:
            raise EmailAlreadyExistsError("Email already exists")
        
        # Hash the password
        hashed_password = self.password_service.hash_password(password)
        
        # Create user record
        user = await self.user_repo.create(
            email=email,
            hashed_password=hashed_password,
            is_verified=is_verified,
            is_admin=is_admin
        )
        
        return user
    
    async def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        password: Optional[str] = None,
        is_verified: Optional[bool] = None,
        is_admin: Optional[bool] = None
    ) -> User:
        """Update user details with partial field updates.
        
        Updates specified fields of a user record while preserving unspecified
        fields. Supports updating email, password, verification status, and
        admin privileges. Passwords are hashed before storage. Email uniqueness
        is enforced.
        
        Args:
            user_id: User's primary key ID
            email: New email address (optional, must be unique if provided)
            password: New password (optional, will be hashed if provided)
            is_verified: New verification status (optional)
            is_admin: New admin status (optional)
            
        Returns:
            Updated User object with all fields populated
            
        Raises:
            ResourceNotFoundError: If user with given ID doesn't exist
            EmailAlreadyExistsError: If new email already taken by another user
            
        Preconditions:
            - user_id > 0 and exists in database
            - If email provided: valid format and not taken by another user
            - If password provided: len(password) >= 8
            - Database connection is active
            
        Postconditions:
            - Only specified fields are modified
            - Unspecified fields retain original values
            - If password updated: hashed before storage
            - If email updated and different: email is updated
            - If is_verified updated: verification status is updated
            - If is_admin updated: admin status is updated
            - updated_at timestamp is refreshed to current time
            
        Requirements:
            - 6.1: Update user with partial fields
            - 6.2: Validate email format if provided
            - 6.3: Reject duplicate email with 409 Conflict
            - 6.4: Hash password if provided
            - 6.5: Never store plain text password
            - 6.8: Preserve unspecified fields
            - 6.9: Refresh updated_at timestamp
            - 6.10: Return 404 if user not found
            - 6.11: Return updated user object
            - 12.2: Enforce email uniqueness on update
        """
        # Fetch existing user
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ResourceNotFoundError(f"User {user_id} not found")
        
        # Prepare update data
        update_data = {}
        
        # Handle email update
        if email is not None and email != user.email:
            # Check if new email is already taken
            existing = await self.user_repo.get_by_email(email)
            if existing is not None:
                raise EmailAlreadyExistsError("Email already exists")
            update_data["email"] = email
        
        # Handle password update
        if password is not None:
            hashed_password = self.password_service.hash_password(password)
            update_data["hashed_password"] = hashed_password
        
        # Handle verification status update
        if is_verified is not None:
            update_data["is_verified"] = is_verified
        
        # Handle admin status update
        if is_admin is not None:
            update_data["is_admin"] = is_admin
        
        # Apply updates if any
        if len(update_data) > 0:
            user = await self.user_repo.update(user, **update_data)
        
        return user
    
    async def delete_user(
        self,
        user_id: int,
        current_admin_id: int
    ) -> None:
        """Delete user account permanently.
        
        Removes a user record from the database. Prevents self-deletion
        by checking if the user being deleted is the current admin.
        
        Args:
            user_id: User's primary key ID to delete
            current_admin_id: Current admin's user ID (for self-deletion check)
            
        Raises:
            ResourceNotFoundError: If user with given ID doesn't exist
            AuthorizationError: If attempting to delete own account
            
        Preconditions:
            - user_id > 0 and exists in database
            - user_id != current_admin_id (cannot delete self)
            - Database connection is active
            
        Postconditions:
            - User record removed from database
            - Operation is irreversible (no soft delete)
            - No return value
            
        Requirements:
            - 7.1: Delete user account
            - 7.2: Return 404 if user not found
            - 7.3: Prevent self-deletion with 403 Forbidden
            - 7.4: Return success response
            - 7.5: Remove user permanently (no soft delete)
        """
        # Fetch user to verify existence
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ResourceNotFoundError(f"User {user_id} not found")
        
        # Prevent self-deletion
        if user_id == current_admin_id:
            raise AuthorizationError("Cannot delete your own account")
        
        # Delete user
        await self.user_repo.delete(user_id)
    
    async def toggle_verification(self, user_id: int) -> User:
        """Toggle user's verification status.
        
        Inverts the is_verified flag for a user (True becomes False, False becomes True).
        Updates the updated_at timestamp to reflect the change.
        
        Args:
            user_id: User's primary key ID
            
        Returns:
            Updated User object with inverted verification status
            
        Raises:
            ResourceNotFoundError: If user with given ID doesn't exist
            
        Preconditions:
            - user_id > 0 and exists in database
            - Database connection is active
            
        Postconditions:
            - is_verified flag is inverted (True -> False, False -> True)
            - updated_at timestamp is refreshed to current time
            - Returns updated User object
            
        Requirements:
            - 8.1: Toggle verification status via PATCH endpoint
            - 8.2: Invert is_verified flag
            - 8.3: Return 404 if user not found
            - 8.4: Refresh updated_at timestamp
            - 8.5: Return updated user object
        """
        # Fetch user
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ResourceNotFoundError(f"User {user_id} not found")
        
        # Toggle verification status
        new_status = not user.is_verified
        user = await self.user_repo.update(user, is_verified=new_status)
        
        return user
