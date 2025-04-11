import random
from datetime import datetime, timedelta
from sqlalchemy import func, select
from app.donation.models import Donation
from app.common.enums import DonationStatus, BloodType
from app.hospital.models import Hospital
from .base_factory import BaseFactory, fake
from .donor_factory import DonorFactory
from .hospital_factory import HospitalFactory
from .blood_request_factory import BloodRequestFactory

class DonationFactory(BaseFactory):
    model = Donation
    
    @classmethod
    def _get_defaults(cls):
        """Generate default donation data"""
        donation_date = datetime.now() + timedelta(
            days=random.randint(-60, 30)  # Allow future scheduled donations
        )
        
        return {
            "blood_amount_ml": random.randint(300, 500),
            "donation_date": donation_date,
            "status": random.choice(list(DonationStatus)),
            "notes": fake.paragraph() if random.random() > 0.5 else None
        }
    
    @classmethod
    async def create_with_relations(cls, session, **kwargs):
        """Create donation with all required relations"""
        # Step 1: Ensure we have a donor
        if "donor_id" not in kwargs and "donor" not in kwargs:
            donor = await DonorFactory.create_with_user(session)
            kwargs["donor_id"] = donor.id
        elif "donor" in kwargs:
            donor = kwargs.pop("donor")
            kwargs["donor_id"] = donor.id
            
        # Step 2: Get donor details if needed
        if "blood_type" not in kwargs and "donor_id" in kwargs:
            stmt = select(DonorFactory.model).where(DonorFactory.model.id == kwargs["donor_id"])
            result = await session.execute(stmt)
            donor = result.scalars().first()
            
            if donor:
                kwargs["blood_type"] = donor.blood_type
            else:
                kwargs["blood_type"] = random.choice(list(BloodType))
        
        # Step 3: Ensure we have a hospital
        if "hospital_id" not in kwargs and "hospital" not in kwargs:
            # First check if there are any hospitals
            stmt = select(func.count()).select_from(Hospital)
            result = await session.execute(stmt)
            hospital_count = result.scalar()
            
            if hospital_count == 0:
                # Create a new hospital if none exist
                hospital = await HospitalFactory.create(session)
            else:
                # Get an existing hospital
                stmt = select(Hospital).order_by(func.random()).limit(1)
                result = await session.execute(stmt)
                hospital = result.scalars().first()
                
            kwargs["hospital_id"] = hospital.id
        elif "hospital" in kwargs:
            hospital = kwargs.pop("hospital")
            kwargs["hospital_id"] = hospital.id
            
        # Step 4: Handle blood request (optional)
        if "blood_request_id" not in kwargs and "blood_request" not in kwargs:
            # 50% chance of linking to a blood request
            if random.random() > 0.5:
                # Create a blood request or get an existing one
                blood_request = await BloodRequestFactory.create_with_relations(
                    session, 
                    hospital_id=kwargs["hospital_id"],
                    blood_type=kwargs.get("blood_type")
                )
                kwargs["blood_request_id"] = blood_request.id
        elif "blood_request" in kwargs:
            blood_request = kwargs.pop("blood_request")
            kwargs["blood_request_id"] = blood_request.id
            
            # If the blood request has a specific blood type, use it
            if "blood_type" not in kwargs and hasattr(blood_request, "blood_type"):
                kwargs["blood_type"] = blood_request.blood_type
        
        # Create and return the donation
        return await cls.create(session, **kwargs)
        
    @classmethod
    async def create_completed_donation(cls, session, **kwargs):
        """Create a completed donation"""
        kwargs["status"] = DonationStatus.COMPLETED
        kwargs["donation_date"] = datetime.now() - timedelta(days=random.randint(1, 30))
        return await cls.create_with_relations(session, **kwargs)
    
    @classmethod
    async def create_scheduled_donation(cls, session, **kwargs):
        """Create a scheduled donation in the future"""
        kwargs["status"] = DonationStatus.SCHEDULED
        kwargs["donation_date"] = datetime.now() + timedelta(days=random.randint(1, 14))
        return await cls.create_with_relations(session, **kwargs)