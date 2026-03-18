"""
Audit logging service for tracking administrative actions.

This module provides the AuditService for recording all administrative
operations performed by admin users for compliance and security purposes.
"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

from app.models.audit_log import AuditLog


class AuditService:
    """Service for audit logging operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize audit service with database session.
        
        Args:
            db: AsyncSession for database operations
        """
        self.db = db
    
    async def log_action(
        self,
        admin_id: int,
        admin_email: str,
        action_type: str,
        target_user_id: int | None = None,
        target_user_email: str | None = None,
        success: bool = True,
        details: str | None = None
    ) -> AuditLog:
        """
        Log an administrative action.
        
        Records an audit log entry for an administrative operation.
        
        Args:
            admin_id: ID of the admin performing the action
            admin_email: Email of the admin performing the action
            action_type: Type of action (create_user, update_user, delete_user, toggle_verify, etc.)
            target_user_id: ID of the user being acted upon (optional)
            target_user_email: Email of the user being acted upon (optional)
            success: Whether the action succeeded (default: True)
            details: Additional details about the action (optional)
            
        Returns:
            AuditLog object that was created
        """
        audit_log = AuditLog(
            admin_id=admin_id,
            admin_email=admin_email,
            action_type=action_type,
            target_user_id=target_user_id,
            target_user_email=target_user_email,
            success=success,
            details=details,
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(audit_log)
        await self.db.flush()
        
        return audit_log
    
    async def log_user_creation(
        self,
        admin_id: int,
        admin_email: str,
        target_user_id: int,
        target_user_email: str,
        success: bool = True,
        details: str | None = None
    ) -> AuditLog:
        """Log user creation action."""
        return await self.log_action(
            admin_id=admin_id,
            admin_email=admin_email,
            action_type="create_user",
            target_user_id=target_user_id,
            target_user_email=target_user_email,
            success=success,
            details=details
        )
    
    async def log_user_update(
        self,
        admin_id: int,
        admin_email: str,
        target_user_id: int,
        target_user_email: str,
        success: bool = True,
        details: str | None = None
    ) -> AuditLog:
        """Log user update action."""
        return await self.log_action(
            admin_id=admin_id,
            admin_email=admin_email,
            action_type="update_user",
            target_user_id=target_user_id,
            target_user_email=target_user_email,
            success=success,
            details=details
        )
    
    async def log_user_deletion(
        self,
        admin_id: int,
        admin_email: str,
        target_user_id: int,
        target_user_email: str,
        success: bool = True,
        details: str | None = None
    ) -> AuditLog:
        """Log user deletion action."""
        return await self.log_action(
            admin_id=admin_id,
            admin_email=admin_email,
            action_type="delete_user",
            target_user_id=target_user_id,
            target_user_email=target_user_email,
            success=success,
            details=details
        )
    
    async def log_verification_toggle(
        self,
        admin_id: int,
        admin_email: str,
        target_user_id: int,
        target_user_email: str,
        success: bool = True,
        details: str | None = None
    ) -> AuditLog:
        """Log verification status toggle action."""
        return await self.log_action(
            admin_id=admin_id,
            admin_email=admin_email,
            action_type="toggle_verify",
            target_user_id=target_user_id,
            target_user_email=target_user_email,
            success=success,
            details=details
        )
    
    async def log_authorization_failure(
        self,
        admin_id: int,
        admin_email: str,
        action_type: str,
        details: str | None = None
    ) -> AuditLog:
        """Log authorization failure."""
        return await self.log_action(
            admin_id=admin_id,
            admin_email=admin_email,
            action_type=action_type,
            success=False,
            details=details or "Authorization failed"
        )
