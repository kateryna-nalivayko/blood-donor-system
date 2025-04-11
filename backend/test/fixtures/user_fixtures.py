import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.models import User
from app.donor.models import Donor
from test.factories.user_factory import UserFactory
from test.factories.donor_factory import DonorFactory

@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession):
    """Create a regular user for testing"""
    return await UserFactory.create(db_session)

@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    """Create an admin user for testing"""
    return await UserFactory.create(
        db_session,
        is_admin=True
    )

@pytest_asyncio.fixture
async def donor_user(db_session: AsyncSession):
    """Create a user with donor role for testing"""
    user = await UserFactory.create(
        db_session, 
        is_donor=True
    )
    donor = await DonorFactory.create(
        db_session,
        user_id=user.id
    )
    return user