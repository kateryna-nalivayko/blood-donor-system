import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from test.factories.user_factory import UserFactory
from test.factories.donor_factory import DonorFactory
from test.factories.hospital_factory import HospitalFactory
from test.factories.hospital_staff_factory import HospitalStaffFactory
from test.factories.blood_request_factory import BloodRequestFactory
from test.factories.donation_factory import DonationFactory
from app.common.enums import BloodType, RequestStatus, DonationStatus

@pytest_asyncio.fixture
async def blood_donation_scenario(db_session: AsyncSession):
    """
    Create a complete blood donation scenario with:
    - Hospital
    - Staff member
    - Donor
    - Blood request
    - Donation linked to the request
    """

    hospital = await HospitalFactory.create(db_session)
    

    staff_user = await UserFactory.create(db_session, is_hospital_staff=True)
    staff = await HospitalStaffFactory.create(
        db_session,
        user_id=staff_user.id,
        hospital_id=hospital.id
    )

    donor_user = await UserFactory.create(db_session, is_donor=True)
    donor = await DonorFactory.create(
        db_session,
        user_id=donor_user.id,
        blood_type=BloodType.A_POSITIVE
    )
    

    blood_request = await BloodRequestFactory.create(
        db_session,
        hospital_id=hospital.id,
        staff_id=staff.id,
        blood_type=BloodType.A_POSITIVE,
        status=RequestStatus.APPROVED
    )
    

    donation = await DonationFactory.create(
        db_session,
        donor_id=donor.id,
        hospital_id=hospital.id,
        blood_request_id=blood_request.id,
        blood_type=BloodType.A_POSITIVE,
        status=DonationStatus.COMPLETED
    )
    

    return {
        "hospital": hospital,
        "staff_user": staff_user,
        "staff": staff,
        "donor_user": donor_user,
        "donor": donor,
        "blood_request": blood_request,
        "donation": donation
    }