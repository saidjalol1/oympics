"""Pytest configuration and fixtures for integration tests."""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.services.password_service import PasswordService


# Configure pytest to not collect classes with these names as test classes
def pytest_configure(config):
    """Configure pytest to ignore specific class names during collection."""
    config.addinivalue_line(
        "python_classes", "!Test !TestRepository !TestService"
    )


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db():
    """Create a test database and return a session."""
    # Override cookie settings for testing
    from app.config import settings
    settings.cookie_secure = False  # Allow cookies over HTTP in tests
    
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async def override_get_db():
        async with async_session() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield async_session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    """Create a test client."""
    from httpx import ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        follow_redirects=True
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_user(test_db):
    """Create an admin user for testing."""
    async with test_db() as session:
        password_service = PasswordService()
        user = User(
            email="admin@example.com",
            hashed_password=password_service.hash_password("adminpass123"),
            is_verified=True,
            is_admin=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def regular_user(test_db):
    """Create a regular user for testing."""
    async with test_db() as session:
        password_service = PasswordService()
        user = User(
            email="user@example.com",
            hashed_password=password_service.hash_password("userpass123"),
            is_verified=True,
            is_admin=False
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
