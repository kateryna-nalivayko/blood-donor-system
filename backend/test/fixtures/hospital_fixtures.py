import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.hospital.models import Hospital
from app.hospital_staff.models import HospitalStaff
from test.factories.hospital_factory import HospitalFactory
from test.factories.hospital_staff_factory import HospitalStaffFactory
from test.factories.user_factory import UserFactory

@pytest_asyncio.fixture
async def hospital(db_session: AsyncSession):
    """Create a hospital for testing"""
    return await HospitalFactory.create(db_session)

@pytest_asyncio.fixture
async def hospital_staff_user(db_session: AsyncSession, hospital):
    """Create a user with hospital staff role for testing"""
    user = await UserFactory.create(
        db_session, 
        is_hospital_staff=True
    )
    staff = await HospitalStaffFactory.create(
        db_session,
        user_id=user.id,
        hospital_id=hospital.id
    )
    return user