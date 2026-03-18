"""
Custom exception classes for the authentication module.

This module defines a hierarchy of exceptions used throughout the application
to handle various error conditions with appropriate HTTP status codes.
"""


class AuthException(Exception):
    """
    Base exception for authentication module.
    
    All custom exceptions in the auth module inherit from this class.
    Each exception includes a message and an HTTP status code.
    """
    
    def __init__(self, message: str, status_code: int = 500) -> None:
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code for the error
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AuthException):
    """
    Raised when input validation fails.
    
    Used for invalid email formats, short passwords, missing fields, etc.
    HTTP Status: 400 Bad Request
    """
    
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)


class AuthenticationError(AuthException):
    """
    Raised when authentication fails.
    
    Used for invalid credentials, missing tokens, etc.
    HTTP Status: 401 Unauthorized
    """
    
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=401)


class AuthorizationError(AuthException):
    """
    Raised when user lacks permission for an action.
    
    Used for unverified users, insufficient permissions, etc.
    HTTP Status: 403 Forbidden
    """
    
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=403)


class ResourceNotFoundError(AuthException):
    """
    Raised when a requested resource doesn't exist.
    
    Used for user not found, token not found, etc.
    HTTP Status: 404 Not Found
    """
    
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=404)


class ResourceConflictError(AuthException):
    """
    Raised when a resource conflicts with existing data.
    
    Used for duplicate email addresses, etc.
    HTTP Status: 409 Conflict
    """
    
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)


class ServiceError(AuthException):
    """
    Raised when an external service fails.
    
    Used for SMTP failures, database connection errors, etc.
    HTTP Status: 503 Service Unavailable
    """
    
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=503)


class InvalidTokenError(AuthenticationError):
    """
    Raised when a token is invalid or malformed.
    
    Used for tokens with invalid signatures, malformed structure, etc.
    """
    pass


class ExpiredTokenError(AuthenticationError):
    """
    Raised when a token has expired.
    
    Used for tokens that are valid but past their expiration time.
    """
    pass


class EmailAlreadyExistsError(ResourceConflictError):
    """
    Raised when attempting to register with an email that already exists.
    """
    pass


class EmailNotVerifiedError(AuthorizationError):
    """
    Raised when a user attempts to login without verifying their email.
    """
    pass


class InvalidCredentialsError(AuthenticationError):
    """
    Raised when login credentials are incorrect.
    """
    pass


class EmailSendError(ServiceError):
    """
    Raised when email sending fails.
    
    Used for SMTP connection failures, invalid email addresses, etc.
    """
    pass
