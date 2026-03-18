"""Custom exception classes for the application.

This module defines custom exceptions used throughout the application
for consistent error handling and reporting.
"""


class ApplicationError(Exception):
    """Base exception for all application errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        """Initialize application error.
        
        Args:
            message: Error message
            status_code: HTTP status code for this error
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ResourceNotFoundError(ApplicationError):
    """Raised when a requested resource is not found."""
    
    def __init__(self, message: str = "Resource not found"):
        """Initialize resource not found error.
        
        Args:
            message: Error message (default: "Resource not found")
        """
        super().__init__(message, status_code=404)


class EmailAlreadyExistsError(ApplicationError):
    """Raised when attempting to create/update user with duplicate email."""
    
    def __init__(self, message: str = "Email already exists"):
        """Initialize email already exists error.
        
        Args:
            message: Error message (default: "Email already exists")
        """
        super().__init__(message, status_code=409)


class AuthorizationError(ApplicationError):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Admin access required"):
        """Initialize authorization error.
        
        Args:
            message: Error message (default: "Admin access required")
        """
        super().__init__(message, status_code=403)
