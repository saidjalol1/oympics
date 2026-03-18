"""
FastAPI application entry point for Quiz Authentication Module.

This module initializes the FastAPI application with all routers,
middleware, exception handlers, and configuration.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth
from app.api import admin
from app.api import test_management
from app.api import client

from app.api.deps import get_current_admin_user
from app.core.exceptions import AuthException, AuthenticationError, AuthorizationError
from app.exceptions import ApplicationError
from app.database import init_db
from app.i18n.language import detect_language
from app.i18n.translations import TranslationManager
from app.models.user import User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize translation manager
translations = TranslationManager()


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    await init_db()
    logger.info("Application started successfully")
    yield
    # Shutdown
    logger.info("Application shutting down")


# Application metadata
app = FastAPI(
    title="Quiz Auth Module",
    description="Multi-language authentication system with email verification",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept-Language"],
)


# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Exception handlers
@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    # Log the error
    logger.warning(f"{exc.__class__.__name__}: {exc.message}")
    
    # For /admin paths, serve login.html
    if request.url.path.startswith("/admin"):
        admin_html_path = Path(__file__).parent / "static" / "admin" / "login.html"
        return FileResponse(
            path=admin_html_path,
            media_type="text/html",
            status_code=401
        )
    
    # For other paths, return JSON
    language = detect_language(request.headers.get("accept-language"))
    localized_message = translations.get(exc.message, language)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": localized_message}
    )


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, exc: AuthorizationError):
    """Handle authorization errors."""
    # Log the error
    logger.warning(f"{exc.__class__.__name__}: {exc.message}")
    
    # For /admin paths, serve 403.html
    if request.url.path.startswith("/admin"):
        admin_html_path = Path(__file__).parent / "static" / "admin" / "403.html"
        return FileResponse(
            path=admin_html_path,
            media_type="text/html",
            status_code=403
        )
    
    # For other paths, return JSON
    language = detect_language(request.headers.get("accept-language"))
    localized_message = translations.get(exc.message, language)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": localized_message}
    )


@app.exception_handler(AuthException)
async def auth_exception_handler(request: Request, exc: AuthException) -> JSONResponse:
    """Handle authentication module exceptions."""
    language = detect_language(request.headers.get("accept-language"))
    localized_message = translations.get(exc.message, language)
    
    # Log based on severity
    if exc.status_code >= 500:
        logger.error(f"{exc.__class__.__name__}: {exc.message}", exc_info=True)
    elif exc.status_code >= 400:
        logger.warning(f"{exc.__class__.__name__}: {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": localized_message}
    )


@app.exception_handler(ApplicationError)
async def application_error_handler(request: Request, exc: ApplicationError):
    """Handle application exceptions."""
    # Log based on severity
    if exc.status_code >= 500:
        logger.error(f"{exc.__class__.__name__}: {exc.message}", exc_info=True)
    elif exc.status_code >= 400:
        logger.warning(f"{exc.__class__.__name__}: {exc.message}")
    
    # For /admin paths with 500 errors, serve 500.html
    if request.url.path.startswith("/admin") and exc.status_code >= 500:
        admin_html_path = Path(__file__).parent / "static" / "admin" / "500.html"
        return FileResponse(
            path=admin_html_path,
            media_type="text/html",
            status_code=exc.status_code
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    language = detect_language(request.headers.get("accept-language"))
    
    # For /admin paths, serve 500.html
    if request.url.path.startswith("/admin"):
        admin_html_path = Path(__file__).parent / "static" / "admin" / "500.html"
        return FileResponse(
            path=admin_html_path,
            media_type="text/html",
            status_code=500
        )
    
    return JSONResponse(
        status_code=500,
        content={"detail": translations.get("internal_error", language)}
    )


# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(test_management.router)
app.include_router(client.router)

# Add login page route (GET /admin/login)
@app.get("/admin/login", include_in_schema=False)
async def serve_login_page() -> FileResponse:
    """
    Serve the admin login page.
    
    Returns the login HTML file for unauthenticated users.
    """
    admin_html_path = Path(__file__).parent / "static" / "admin" / "login.html"
    
    return FileResponse(
        path=admin_html_path,
        media_type="text/html",
        status_code=200
    )


# Add error page routes
@app.get("/admin/404", include_in_schema=False)
async def serve_404_page() -> FileResponse:
    """Serve the 404 error page."""
    admin_html_path = Path(__file__).parent / "static" / "admin" / "404.html"
    
    return FileResponse(
        path=admin_html_path,
        media_type="text/html",
        status_code=404
    )


@app.get("/admin/500", include_in_schema=False)
async def serve_500_page() -> FileResponse:
    """Serve the 500 error page."""
    admin_html_path = Path(__file__).parent / "static" / "admin" / "500.html"
    
    return FileResponse(
        path=admin_html_path,
        media_type="text/html",
        status_code=500
    )


@app.get("/admin/403", include_in_schema=False)
async def serve_403_page() -> FileResponse:
    """Serve the 403 error page."""
    admin_html_path = Path(__file__).parent / "static" / "admin" / "403.html"
    
    return FileResponse(
        path=admin_html_path,
        media_type="text/html",
        status_code=403
    )


# Add admin panel route (GET /admin) - redirect to users page
@app.get("/admin", include_in_schema=False)
async def serve_admin_panel(
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
) -> RedirectResponse:
    """
    Redirect to the users management page as the default admin page.
    
    **Requirements:**
    - 1.1: Serve admin panel HTML interface at /admin
    - 1.2: Redirect non-authenticated users to login with 401
    - 1.3: Deny non-admin users with 403
    - 9.1: Non-admin users cannot access
    - 9.2: Unauthenticated users cannot access
    - 9.3: Verify admin status from database
    """
    return RedirectResponse(url="/admin/users", status_code=302)


# Test Management Page Routes
@app.get("/admin/users", include_in_schema=False)
async def serve_users_page(
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
) -> FileResponse:
    """
    Serve the users management page.
    
    Provides interface for managing platform users with CRUD operations.
    Requires admin authentication.
    """
    users_html_path = Path(__file__).parent / "static" / "admin" / "users.html"
    return FileResponse(
        path=users_html_path,
        media_type="text/html",
        status_code=200
    )


@app.get("/admin/audit", include_in_schema=False)
async def serve_audit_page(
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
) -> FileResponse:
    """
    Serve the audit logs page.
    
    Provides interface for viewing system audit logs and user actions.
    Requires admin authentication.
    """
    audit_html_path = Path(__file__).parent / "static" / "admin" / "audit.html"
    return FileResponse(
        path=audit_html_path,
        media_type="text/html",
        status_code=200
    )


@app.get("/admin/subjects", include_in_schema=False)
async def serve_subjects_page(
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
) -> FileResponse:
    """
    Serve the subjects management page.
    
    Provides interface for managing test subjects with multi-language support.
    Requires admin authentication.
    """
    subjects_html_path = Path(__file__).parent / "static" / "admin" / "subjects.html"
    return FileResponse(
        path=subjects_html_path,
        media_type="text/html",
        status_code=200
    )


@app.get("/admin/levels", include_in_schema=False)
async def serve_levels_page(
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
) -> FileResponse:
    """
    Serve the levels management page.
    
    Provides interface for managing test levels with multi-language support.
    Requires admin authentication.
    """
    levels_html_path = Path(__file__).parent / "static" / "admin" / "levels.html"
    return FileResponse(
        path=levels_html_path,
        media_type="text/html",
        status_code=200
    )


@app.get("/admin/tests", include_in_schema=False)
async def serve_tests_page(
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
) -> FileResponse:
    """
    Serve the tests management page.
    
    Provides interface for managing tests with pricing, dates, and multi-language support.
    Requires admin authentication.
    """
    tests_html_path = Path(__file__).parent / "static" / "admin" / "tests.html"
    return FileResponse(
        path=tests_html_path,
        media_type="text/html",
        status_code=200
    )


@app.get("/admin/questions", include_in_schema=False)
async def serve_questions_page(
    current_admin: Annotated[User, Depends(get_current_admin_user)] = None,
) -> FileResponse:
    """
    Serve the questions management page.
    
    Provides interface for managing questions with options, images, and multi-language support.
    Requires admin authentication.
    """
    questions_html_path = Path(__file__).parent / "static" / "admin" / "questions.html"
    return FileResponse(
        path=questions_html_path,
        media_type="text/html",
        status_code=200
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Add 404 handler for unmatched /admin routes
@app.api_route("/{path_name:path}", methods=["GET"], include_in_schema=False)
async def catch_all_admin_routes(path_name: str, request: Request):
    """Catch unmatched routes starting with /admin and serve 404.html."""
    if path_name.startswith("admin"):
        admin_html_path = Path(__file__).parent / "static" / "admin" / "404.html"
        return FileResponse(
            path=admin_html_path,
            media_type="text/html",
            status_code=404
        )
    
    # For non-admin paths, return JSON 404
    return JSONResponse(
        status_code=404,
        content={"detail": "Not found"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
