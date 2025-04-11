import random
from app.hospital.models import Hospital
from app.common.enums import HospitalType
from test.factories.user_factory import UserFactory
from .base_factory import BaseFactory, fake

class HospitalFactory(BaseFactory):
    model = Hospital
    
    @classmethod
    def _get_defaults(cls):
        """Generate default hospital data"""
        city = fake.city()
        region = fake.region()

        @classmethod
        async def create_with_relations(cls, session, **kwargs):
            """Create hospital staff with associated user and hospital"""
            if "hospital_id" not in kwargs and "hospital" not in kwargs:
                hospital = await HospitalFactory.create(session)
                kwargs["hospital_id"] = hospital.id
            elif "hospital" in kwargs:
                hospital = kwargs.pop("hospital")
                kwargs["hospital_id"] = hospital.id
                
            if "user_id" not in kwargs and "user" not in kwargs:
                user = await UserFactory.create_hospital_staff_user(session)
                kwargs["user_id"] = user.id
            elif "user" in kwargs:
                user = kwargs.pop("user")
                kwargs["user_id"] = user.id
                # Make sure the user is marked as hospital staff
                user.is_hospital_staff = True
                await session.flush()
                
            return await cls.create(session, **kwargs)
        
        return {
            "name": f"{fake.company()} {'Лікарня' if random.random() > 0.5 else 'Клініка'}",
            "hospital_type": random.choice(list(HospitalType)),
            "address": fake.street_address(),
            "city": city,
            "region": region,
            "country": "Ukraine",
            "phone_number": f"+380{fake.numerify('#########')}",
            "email": f"info@{fake.domain_word()}.ua",
            "website": f"https://www.{fake.domain_word()}.ua"
        }