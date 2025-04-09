import sys
import os
import httpx
from sqlalchemy import delete
from app.config import Settings
from app.users.models import User
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import ASGITransport, AsyncClient
from app.main import app
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.database import Base


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_users_dao():
    with patch("app.users.dao.UsersDAO") as mock_dao:
        mock_dao.find_one_or_none = AsyncMock(return_value=None)
        mock_dao.add = AsyncMock(return_value=None)
        mock_dao.update = AsyncMock(return_value=None)
        mock_dao.delete = AsyncMock(return_value=None)
        yield mock_dao


async def init_db():
    test_settings = Settings(
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_NAME="test_blood_donor",  
        DB_USER="kate-nalivayko",
        DB_PASSWORD="book"
    )
    
    DATABASE_URL = f"postgresql+asyncpg://{test_settings.DB_USER}:{test_settings.DB_PASSWORD}@{test_settings.DB_HOST}:{test_settings.DB_PORT}/{test_settings.DB_NAME}"
    
    engine = create_async_engine(DATABASE_URL)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    return async_session_maker


@pytest_asyncio.fixture
async def default_client():
    """Create a test client with database initialization"""
    session_maker = await init_db()
    

    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        yield ac
        

        # async with session_maker() as session:
        #     await session.execute(delete(User))
        #     await session.commit()