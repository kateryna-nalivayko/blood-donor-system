import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import ASGITransport, AsyncClient
from app.main import app


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