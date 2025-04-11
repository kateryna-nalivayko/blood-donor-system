import asyncio
import random
from sqlalchemy import select
from app.database import async_session_maker

from test.factories.user_factory import UserFactory
from test.factories.hospital_factory import HospitalFactory
from test.factories.donor_factory import DonorFactory
from test.factories.hospital_staff_factory import HospitalStaffFactory
from test.factories.blood_request_factory import BloodRequestFactory
from test.factories.donation_factory import DonationFactory

async def generate_test_data(
    user_count=1000,
    hospital_count=200,
    donor_percentage=0.4,  # 40% of users are donors
    staff_percentage=0.15,  # 15% of users are staff
    requests_per_staff=2,
    donations_per_donor=1.5  # Average 1.5 donations per donor
):
    """Generate consistent test data respecting all relationships"""
    async with async_session_maker() as session:
        # Step 1: Create base users
        print(f"Creating {user_count} users...")
        users = []
        for _ in range(user_count):
            user = await UserFactory.create(session)
            users.append(user)
            
        # Step 2: Create hospitals
        print(f"Creating {hospital_count} hospitals...")
        hospitals = []
        for _ in range(hospital_count):
            hospital = await HospitalFactory.create(session)
            hospitals.append(hospital)
            
        # Step 3: Create donors from a subset of users
        donor_count = int(user_count * donor_percentage)
        print(f"Creating {donor_count} donors...")
        donors = []
        user_indices = random.sample(range(user_count), donor_count)
        
        for idx in user_indices:
            user = users[idx]
            donor = await DonorFactory.create(
                session,
                user_id=user.id
            )
            # Update user flags
            user.is_donor = True
            donors.append(donor)
            
        # Step 4: Create hospital staff from another subset of users
        staff_count = int(user_count * staff_percentage)
        print(f"Creating {staff_count} hospital staff members...")
        staff_members = []
        # Get users who are not donors
        available_users = [u for i, u in enumerate(users) if i not in user_indices]
        staff_user_count = min(staff_count, len(available_users))
        
        for i in range(staff_user_count):
            user = available_users[i]
            hospital = hospitals[i % len(hospitals)]
            
            staff = await HospitalStaffFactory.create(
                session,
                user_id=user.id,
                hospital_id=hospital.id
            )
            # Update user flags
            user.is_hospital_staff = True
            staff_members.append(staff)
            
        # Commit to ensure all base entities are saved
        await session.commit()
            
        # Step 5: Create blood requests
        print("Creating blood requests...")
        requests = []
        for staff in staff_members:
            for _ in range(requests_per_staff):
                request = await BloodRequestFactory.create_with_relations(
                    session, 
                    hospital_id=staff.hospital_id,
                    staff_id=staff.id
                )
                requests.append(request)
        

        print("Creating donations...")
        donations = []
        

        for i, request in enumerate(requests):
            if i < len(donors):
                donation = await DonationFactory.create_with_relations(
                    session,
                    donor_id=donors[i].id,
                    hospital_id=request.hospital_id,
                    blood_request_id=request.id,
                    blood_type=request.blood_type
                )
                donations.append(donation)
        

        total_additional_donations = int(donor_count * donations_per_donor) - len(donations)
        for _ in range(total_additional_donations):
            donor = random.choice(donors)
            hospital = random.choice(hospitals)
            
            donation = await DonationFactory.create_with_relations(
                session,
                donor_id=donor.id,
                hospital_id=hospital.id
            )
            donations.append(donation)
        

        await session.commit()
        

        print(f"""
Test data generation complete!
Generated:
- {len(users)} users
- {len(hospitals)} hospitals
- {len(donors)} donors
- {len(staff_members)} hospital staff
- {len(requests)} blood requests
- {len(donations)} donations
        """)
        
        return {
            "users": users,
            "hospitals": hospitals,
            "donors": donors,
            "staff": staff_members,
            "requests": requests,
            "donations": donations
        }

if __name__ == "__main__":
    asyncio.run(generate_test_data())