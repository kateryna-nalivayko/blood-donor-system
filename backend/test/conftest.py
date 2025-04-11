# import sys
# import os
# import httpx
# from sqlalchemy import delete
# from app.config import Settings
# from app.users.models import User
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# import pytest
# import pytest_asyncio
# from unittest.mock import AsyncMock, patch, MagicMock
# from httpx import ASGITransport, AsyncClient
# from app.main import app
# import asyncio

# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
# from app.database import Base


# @pytest_asyncio.fixture
# async def client():
#     async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
#         yield client


# @pytest.fixture
# def mock_users_dao():
#     with patch("app.users.dao.UsersDAO") as mock_dao:
#         mock_dao.find_one_or_none = AsyncMock(return_value=None)
#         mock_dao.add = AsyncMock(return_value=None)
#         mock_dao.update = AsyncMock(return_value=None)
#         mock_dao.delete = AsyncMock(return_value=None)
#         yield mock_dao


# async def init_db():
#     test_settings = Settings(
#         DB_HOST="localhost",
#         DB_PORT=5432,
#         DB_NAME="test_blood_donor",  
#         DB_USER="kate-nalivayko",
#         DB_PASSWORD="book"
#     )
    
#     DATABASE_URL = f"postgresql+asyncpg://{test_settings.DB_USER}:{test_settings.DB_PASSWORD}@{test_settings.DB_HOST}:{test_settings.DB_PORT}/{test_settings.DB_NAME}"
    
#     engine = create_async_engine(DATABASE_URL)
#     async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)
#         await conn.run_sync(Base.metadata.create_all)
    
#     return async_session_maker


# @pytest_asyncio.fixture
# async def default_client():
#     """Create a test client with database initialization"""
#     session_maker = await init_db()
    

#     async with AsyncClient(
#         transport=ASGITransport(app=app), 
#         base_url="http://test"
#     ) as ac:
#         yield ac
        

#         # async with session_maker() as session:
#         #     await session.execute(delete(User))
#         #     await session.commit()



import sys
import os
import pytest
import pytest_asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# Add the parent directory to the path so we can import the app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import DATABASE_URL, Base

# Import all fixtures
from test.fixtures.user_fixtures import *
from test.fixtures.hospital_fixtures import *
from test.fixtures.scenario_fixtures import *

from app.config import Settings

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Create a test database engine using PostgreSQL"""

    test_settings = Settings(
        DB_HOST=os.environ.get("TEST_DB_HOST", "localhost"),
        DB_PORT=int(os.environ.get("TEST_DB_PORT", "5432")),
        DB_NAME=os.environ.get("TEST_DB_NAME", "test_blood_donor"),  
        DB_USER=os.environ.get("TEST_DB_USER", "kate-nalivayko"),
        DB_PASSWORD=os.environ.get("TEST_DB_PASSWORD", "book")
    )
    
    TEST_DATABASE_URL = f"postgresql+asyncpg://{test_settings.DB_USER}:{test_settings.DB_PASSWORD}@{test_settings.DB_HOST}:{test_settings.DB_PORT}/{test_settings.DB_NAME}"
    
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create a test database session"""
    async_session = async_sessionmaker(db_engine, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture(autouse=True)
async def transactional_tests(db_session):
    """Automatically wrap all tests in transactions that get rolled back"""
    yield


@pytest_asyncio.fixture(scope="session")
async def real_db_session():
    """Create a session for testing with the real database (use with care)"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        yield session