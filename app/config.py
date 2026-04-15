"""
Configuration module for Quiz Auth Module.

This module loads and validates all environment variables using Pydantic Settings.
It provides type-safe access to configuration values throughout the application.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings are loaded from the .env file or environment variables.
    Required fields will raise validation errors if not provided.
    """
    
    # Application settings
    app_name: str = Field(default="Quiz Auth Module", description="Application name")
    debug: bool = Field(default=False, description="Debug mode flag")
    environment: str = Field(default="production", description="Environment (development/production)")
    
    # Database settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///./quiz_auth.db",
        description="Database connection URL"
    )
    
    # Security settings
    secret_key: str = Field(..., description="Secret key for JWT token signing (min 32 chars)")
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(
        default=15,
        description="Access token expiration time in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )
    verification_token_expire_hours: int = Field(
        default=24,
        description="Email verification token expiration time in hours"
    )
    
    # Password settings
    bcrypt_rounds: int = Field(
        default=12,
        description="Bcrypt cost factor for password hashing"
    )
    
    # Email/SMTP settings
    smtp_host: str = Field(..., description="SMTP server hostname")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str = Field(..., description="SMTP authentication username")
    smtp_password: str = Field(..., description="SMTP authentication password")
    smtp_from_email: str = Field(..., description="Email address for outgoing emails")
    
    # Click Payment settings
    click_service_id: int = Field(default=99674, description="Click service ID")
    click_merchant_id: int = Field(default=59143, description="Click merchant ID")
    click_secret_key: str = Field(default="0MIYh977pjNF6", description="Click secret key")
    click_merchant_user_id: int = Field(default=81820, description="Click merchant user ID")

    # Frontend settings
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Frontend application URL for redirects"
    )
    
    # Cookie settings
    cookie_name: str = Field(
        default="session",
        description="Session cookie name"
    )
    cookie_max_age: int = Field(
        default=604800,
        description="Session cookie max age in seconds (7 days)"
    )
    cookie_path: str = Field(
        default="/",
        description="Session cookie path"
    )
    cookie_domain: str | None = Field(
        default=None,
        description="Session cookie domain (None for current domain)"
    )
    cookie_secure: bool = Field(
        default=True,
        description="Session cookie secure flag (HTTPS only in production)"
    )
    cookie_httponly: bool = Field(
        default=True,
        description="Session cookie HttpOnly flag (prevent JavaScript access)"
    )
    cookie_samesite: str = Field(
        default="Lax",
        description="Session cookie SameSite attribute (Strict/Lax/None)"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
