import random
from datetime import date, timedelta
from app.donor.models import Donor, Gender
from app.common.enums import BloodType
from .base_factory import BaseFactory, fake
from .user_factory import UserFactory

class DonorFactory(BaseFactory):
    model = Donor
    
    @classmethod
    def _get_defaults(cls):
        """Generate default donor data"""
        # Generate a birth date for someone between 18 and 65
        birth_date = fake.date_of_birth(minimum_age=18, maximum_age=65)
        
        # Random blood type
        blood_types = list(BloodType)
        
        return {
            "gender": random.choice(list(Gender)),
            "date_of_birth": birth_date,
            "blood_type": random.choice(blood_types),
            "weight": round(random.uniform(50.0, 120.0), 1),  # Weight in kg
            "height": round(random.uniform(155.0, 195.0), 1),  # Height in cm
            "is_eligible": True,
            "total_donations": 0
        }
    
    @classmethod
    async def create_with_user(cls, session, **kwargs):
        """Create a donor with an associated user"""
        if "user_id" not in kwargs and "user" not in kwargs:
            # Create a new donor user
            user = await UserFactory.create_donor_user(session)
            kwargs["user_id"] = user.id
        elif "user" in kwargs:
            user = kwargs.pop("user")
            kwargs["user_id"] = user.id
            # Make sure the user is marked as a donor
            user.is_donor = True
            await session.flush()
            
        return await cls.create(session, **kwargs)