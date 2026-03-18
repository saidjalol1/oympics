"""
Admin panel API endpoints.

This module implements the admin endpoints for user management, including
listing, creating, updating, deleting, and verifying users. All endpoints
require admin authentication via the get_current_admin_user dependency.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.database import get_db
from app.exceptions import (
    AuthorizationError,
    EmailAlreadyExistsError,
    ResourceNotFoundError,
)
from app.models.user import User
from app.schemas.admin import (
    AdminActionResponse,
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    AdminUserResponse,
    UserListQueryParams,
    UserListResponse,
)
from app.services.admin_service import AdminService
from app.services.password_service import PasswordService
from app.repositories.user_repository import UserRepository

# Initialize router
router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get(
    "/users",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "User list retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "users": [
                            {
                                "id": 1,
                                "email": "user@example.com",
                                "is_verified": True,
                                "is_admin": False,
                                "created_at": "2024-01-15T10:30:00",
                                "updated_at": "2024-01-15T10:30:00"
                            }
                        ],
                        "total": 100,
                        "skip": 0,
                        "limit": 50
                    }
                }
            }
        },
        400: {
            "description": "Validation error (invalid pagination parameters)",
        },
        401: {
            "description": "Unauthorized - authentication required",
        },
        403: {
            "description": "Forbidden - admin access required",
        },
    },
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    search: str | None = Query(None, description="Email search filter"),
    verified_only: bool | None = Query(None, description="Filter by verification status"),
    is_admin: bool | None = Query(None, description="Filter by admin status"),
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """
    List all users with pagination and filtering.
    
    Retrieves a paginated list of users with optional email search,
    verification status filtering, and admin status filtering. Results are 
    ordered by created_at descending.
    
    **Query Parameters:**
    - skip: Number of records to skip (default: 0, must be >= 0)
    - limit: Maximum records to return (default: 50, must be 1-100)
    - search: Email search filter (case-insensitive partial match, optional)
    - verified_only: Filter by verification status (True/False/None, optional)
    - is_admin: Filter by admin status (True/False/None, optional)
    
    **Requirements:**
    - 2.1: Return paginated users with total count
    - 2.2: Apply skip/limit pagination
    - 2.3: Use default values (skip=0, limit=50)
    - 2.4: Reject limit > 100
    - 2.5: Reject skip < 0
    - 2.6: Order by created_at DESC
    - 2.7: Include id, email, is_verified, is_admin, timestamps
    - 2.8: Never include hashed_password
    - 2.9: Return accurate total count
    - 3.1: Search by email (case-insensitive)
    - 3.2: Filter by verified_only=true
    - 3.3: Filter by verified_only=false
    - 3.4: Combine search and filter with AND logic
    - 3.5: Treat empty search as no filter
    - 3.6: Return all users without filtering if no params
    - 3.7: Return accurate total count matching filters
    - 9.1: Non-admin users cannot access
    - 9.2: Unauthenticated users cannot access
    - 9.3: Verify admin status from database
    """
    # Treat empty search string as no search
    if search is not None and len(search.strip()) == 0:
        search = None
    
    # Create service and fetch users
    user_repo = UserRepository(db)
    admin_service = AdminService(user_repo, PasswordService())
    
    users, total = await admin_service.get_all_users(
        skip=skip,
        limit=limit,
        search=search,
        verified_only=verified_only,
        is_admin=is_admin
    )
    
    # Convert to response schema
    user_responses = [AdminUserResponse.model_validate(user) for user in users]
    
    return UserListResponse(
        users=user_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/users/{user_id}",
    response_model=AdminUserResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "User retrieved successfully",
        },
        401: {
            "description": "Unauthorized - authentication required",
        },
        403: {
            "description": "Forbidden - admin access required",
        },
        404: {
            "description": "User not found",
        },
    },
)
async def get_user(
    user_id: int,
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    """
    Get a single user by ID.
    
    Retrieves detailed information about a specific user.
    
    **Path Parameters:**
    - user_id: The user's unique identifier
    
    **Requirements:**
    - 5.1: Return user with all details
    - 5.2: Return 404 if user not found
    - 5.3: Include id, email, is_verified, is_admin, timestamps
    - 5.4: Never include hashed_password
    - 9.1: Non-admin users cannot access
    - 9.2: Unauthenticated users cannot access
    - 9.3: Verify admin status from database
    """
    user_repo = UserRepository(db)
    admin_service = AdminService(user_repo, PasswordService())
    
    user = await admin_service.get_user_by_id(user_id)
    
    return AdminUserResponse.model_validate(user)


@router.post(
    "/users",
    response_model=AdminActionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "User created successfully",
        },
        400: {
            "description": "Validation error (invalid email or password)",
        },
        401: {
            "description": "Unauthorized - authentication required",
        },
        403: {
            "description": "Forbidden - admin access required",
        },
        409: {
            "description": "Email already exists",
        },
    },
)
async def create_user(
    request: AdminCreateUserRequest,
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
    db: AsyncSession = Depends(get_db),
) -> AdminActionResponse:
    """
    Create a new user account.
    
    Creates a new user with the provided email and password. The admin can
    optionally set the verification status and admin privileges directly,
    bypassing email verification.
    
    **Request Body:**
    - email: Valid email address (required)
    - password: Password 8-100 characters (required)
    - is_verified: Pre-verify email (optional, default: false)
    - is_admin: Grant admin privileges (optional, default: false)
    
    **Requirements:**
    - 4.1: Create new user account
    - 4.2: Hash password using bcrypt
    - 4.3: Never store plain text password
    - 4.4: Set is_verified as provided (admin bypass)
    - 4.5: Set is_verified as provided
    - 4.6: Set created_at and updated_at to current time
    - 4.7: Reject duplicate email with 409
    - 4.8: Reject invalid email format with 400
    - 4.9: Reject password < 8 chars with 400
    - 4.10: Reject password > 100 chars with 400
    - 4.11: Return created user object
    - 9.1: Non-admin users cannot access
    - 9.2: Unauthenticated users cannot access
    - 9.3: Verify admin status from database
    - 10.1: Validate email format
    - 10.3: Validate required fields
    - 12.1: Enforce email uniqueness
    """
    from app.services.audit_service import AuditService
    
    # Eagerly load admin attributes to avoid lazy loading issues in exception handlers
    admin_id = current_admin.id
    admin_email = current_admin.email
    
    user_repo = UserRepository(db)
    password_service = PasswordService()
    admin_service = AdminService(user_repo, password_service)
    audit_service = AuditService(db)
    
    try:
        user = await admin_service.create_user(
            email=request.email,
            password=request.password,
            is_verified=request.is_verified,
            is_admin=request.is_admin
        )
        
        # Log successful action
        await audit_service.log_user_creation(
            admin_id=admin_id,
            admin_email=admin_email,
            target_user_id=user.id,
            target_user_email=user.email,
            success=True
        )
        
        await db.commit()
        
        return AdminActionResponse(
            message="User created successfully",
            user=AdminUserResponse.model_validate(user)
        )
    except Exception as e:
        await db.rollback()
        # Log failed action
        await audit_service.log_user_creation(
            admin_id=admin_id,
            admin_email=admin_email,
            target_user_id=0,
            target_user_email=request.email,
            success=False,
            details=str(e)
        )
        await db.commit()
        raise


@router.put(
    "/users/{user_id}",
    response_model=AdminActionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "User updated successfully",
        },
        400: {
            "description": "Validation error (invalid email or password)",
        },
        401: {
            "description": "Unauthorized - authentication required",
        },
        403: {
            "description": "Forbidden - admin access required",
        },
        404: {
            "description": "User not found",
        },
        409: {
            "description": "Email already exists",
        },
    },
)
async def update_user(
    user_id: int,
    request: AdminUpdateUserRequest,
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
    db: AsyncSession = Depends(get_db),
) -> AdminActionResponse:
    """
    Update user details with partial field updates.
    
    Updates specified user fields. Only fields included in the request are
    modified; unspecified fields retain their original values.
    
    **Path Parameters:**
    - user_id: The user's unique identifier
    
    **Request Body (all optional):**
    - email: New email address
    - password: New password (8-100 characters)
    - is_verified: New verification status
    - is_admin: New admin status
    
    **Requirements:**
    - 6.1: Update only specified fields
    - 6.2: Validate email format if provided
    - 6.3: Reject duplicate email with 409
    - 6.4: Hash password if provided
    - 6.5: Never store plain text password
    - 6.6: Reject password < 8 chars with 400
    - 6.7: Update is_verified if provided
    - 6.8: Preserve unspecified fields
    - 6.9: Refresh updated_at timestamp
    - 6.10: Return 404 if user not found
    - 6.11: Return updated user object
    - 9.1: Non-admin users cannot access
    - 9.2: Unauthenticated users cannot access
    - 9.3: Verify admin status from database
    - 10.1: Validate email format
    - 12.2: Enforce email uniqueness
    """
    from app.services.audit_service import AuditService
    
    # Eagerly load admin attributes to avoid lazy loading issues in exception handlers
    admin_id = current_admin.id
    admin_email = current_admin.email
    
    user_repo = UserRepository(db)
    password_service = PasswordService()
    admin_service = AdminService(user_repo, password_service)
    audit_service = AuditService(db)
    
    try:
        user = await admin_service.update_user(
            user_id=user_id,
            email=request.email,
            password=request.password,
            is_verified=request.is_verified,
            is_admin=request.is_admin
        )
        
        # Log successful action
        await audit_service.log_user_update(
            admin_id=admin_id,
            admin_email=admin_email,
            target_user_id=user.id,
            target_user_email=user.email,
            success=True
        )
        
        await db.commit()
        
        return AdminActionResponse(
            message="User updated successfully",
            user=AdminUserResponse.model_validate(user)
        )
    except Exception as e:
        await db.rollback()
        # Log failed action
        await audit_service.log_user_update(
            admin_id=admin_id,
            admin_email=admin_email,
            target_user_id=user_id,
            target_user_email="",
            success=False,
            details=str(e)
        )
        await db.commit()
        raise


@router.delete(
    "/users/{user_id}",
    response_model=AdminActionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "User deleted successfully",
        },
        401: {
            "description": "Unauthorized - authentication required",
        },
        403: {
            "description": "Forbidden - admin access required or self-deletion attempted",
        },
        404: {
            "description": "User not found",
        },
    },
)
async def delete_user(
    user_id: int,
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
    db: AsyncSession = Depends(get_db),
) -> AdminActionResponse:
    """
    Delete a user account.
    
    Permanently removes a user from the system. Admins cannot delete their
    own account.
    
    **Path Parameters:**
    - user_id: The user's unique identifier
    
    **Requirements:**
    - 7.1: Remove user from database
    - 7.2: Return 404 if user not found
    - 7.3: Reject self-deletion with 403
    - 7.4: Return success response
    - 7.5: Remove permanently (no soft delete)
    - 9.1: Non-admin users cannot access
    - 9.2: Unauthenticated users cannot access
    - 9.3: Verify admin status from database
    """
    from app.services.audit_service import AuditService
    
    # Eagerly load admin attributes to avoid lazy loading issues in exception handlers
    admin_id = current_admin.id
    admin_email = current_admin.email
    
    user_repo = UserRepository(db)
    password_service = PasswordService()
    admin_service = AdminService(user_repo, password_service)
    audit_service = AuditService(db)
    
    try:
        # Get user before deletion for audit log
        user = await admin_service.get_user_by_id(user_id)
        
        await admin_service.delete_user(user_id, admin_id)
        
        # Log successful action
        await audit_service.log_user_deletion(
            admin_id=admin_id,
            admin_email=admin_email,
            target_user_id=user.id,
            target_user_email=user.email,
            success=True
        )
        
        await db.commit()
        
        return AdminActionResponse(
            message="User deleted successfully",
            user=None
        )
    except Exception as e:
        await db.rollback()
        # Log failed action
        await audit_service.log_user_deletion(
            admin_id=admin_id,
            admin_email=admin_email,
            target_user_id=user_id,
            target_user_email="",
            success=False,
            details=str(e)
        )
        await db.commit()
        raise


@router.patch(
    "/users/{user_id}/verify",
    response_model=AdminActionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Verification status toggled successfully",
        },
        401: {
            "description": "Unauthorized - authentication required",
        },
        403: {
            "description": "Forbidden - admin access required",
        },
        404: {
            "description": "User not found",
        },
    },
)
async def toggle_verification(
    user_id: int,
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
    db: AsyncSession = Depends(get_db),
) -> AdminActionResponse:
    """
    Toggle user verification status.
    
    Inverts the user's email verification status (True becomes False, False becomes True).
    
    **Path Parameters:**
    - user_id: The user's unique identifier
    
    **Requirements:**
    - 8.1: Toggle verification status
    - 8.2: Invert is_verified flag
    - 8.3: Return 404 if user not found
    - 8.4: Refresh updated_at timestamp
    - 8.5: Return updated user object
    - 9.1: Non-admin users cannot access
    - 9.2: Unauthenticated users cannot access
    - 9.3: Verify admin status from database
    """
    from app.services.audit_service import AuditService
    
    # Eagerly load admin attributes to avoid lazy loading issues in exception handlers
    admin_id = current_admin.id
    admin_email = current_admin.email
    
    user_repo = UserRepository(db)
    password_service = PasswordService()
    admin_service = AdminService(user_repo, password_service)
    audit_service = AuditService(db)
    
    try:
        user = await admin_service.toggle_verification(user_id)
        
        # Log successful action
        await audit_service.log_verification_toggle(
            admin_id=admin_id,
            admin_email=admin_email,
            target_user_id=user.id,
            target_user_email=user.email,
            success=True,
            details=f"Verification status toggled to {user.is_verified}"
        )
        
        await db.commit()
        
        return AdminActionResponse(
            message="Verification status toggled successfully",
            user=AdminUserResponse.model_validate(user)
        )
    except Exception as e:
        await db.rollback()
        # Log failed action
        await audit_service.log_verification_toggle(
            admin_id=admin_id,
            admin_email=admin_email,
            target_user_id=user_id,
            target_user_email="",
            success=False,
            details=str(e)
        )
        await db.commit()
        raise


@router.get(
    "/audit-logs",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Audit logs retrieved successfully",
        },
        401: {
            "description": "Not authenticated",
        },
        403: {
            "description": "Not authorized",
        },
    },
)
async def get_audit_logs(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    action_type: Annotated[str | None, Query()] = None,
    admin_email: Annotated[str | None, Query()] = None,
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get audit logs with optional filtering.
    
    **Parameters:**
    - skip: Number of records to skip (pagination)
    - limit: Number of records to return (max 100)
    - action_type: Filter by action type (create_user, update_user, delete_user, etc.)
    - admin_email: Filter by admin email
    
    **Requirements:**
    - Admin authentication required
    - Returns paginated audit logs
    """
    from app.models.audit_log import AuditLog
    from sqlalchemy import select, desc, func
    
    try:
        # Build base query for filtering
        base_query = select(AuditLog)
        
        # Apply filters
        if action_type:
            base_query = base_query.where(AuditLog.action_type == action_type)
        if admin_email:
            base_query = base_query.where(AuditLog.admin_email.ilike(f"%{admin_email}%"))
        
        # Get total count with filters
        count_query = select(func.count()).select_from(AuditLog)
        if action_type:
            count_query = count_query.where(AuditLog.action_type == action_type)
        if admin_email:
            count_query = count_query.where(AuditLog.admin_email.ilike(f"%{admin_email}%"))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Order by created_at descending (newest first) and apply pagination
        query = base_query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        audit_logs = result.scalars().all()
        
        # Format response
        logs_data = [
            {
                "id": log.id,
                "admin_id": log.admin_id,
                "admin_email": log.admin_email,
                "action_type": log.action_type,
                "target_user_id": log.target_user_id,
                "target_user_email": log.target_user_email,
                "success": log.success,
                "details": log.details,
                "created_at": log.created_at.isoformat(),
            }
            for log in audit_logs
        ]
        
        return {
            "logs": logs_data,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
