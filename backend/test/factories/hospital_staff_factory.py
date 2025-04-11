import random
from app.hospital_staff.models import HospitalStaff
from app.common.enums import StaffRole, Department
from .base_factory import BaseFactory
from .user_factory import UserFactory
from .hospital_factory import HospitalFactory

class HospitalStaffFactory(BaseFactory):
    model = HospitalStaff
    
    @classmethod
    def _get_defaults(cls):
        """Generate default hospital staff data"""
        return {
            "role": random.choice(list(StaffRole)),
            "department": random.choice(list(Department))
        }
    
    @classmethod
    async def create_with_relations(cls, session, **kwargs):
        """Create hospital staff with associated user and hospital"""
        if "hospital_id" not in kwargs:
            hospital = await HospitalFactory.create(session)
            kwargs["hospital_id"] = hospital.id
            
        if "user_id" not in kwargs:
            user = await UserFactory.create(session, is_hospital_staff=True)
            kwargs["user_id"] = user.id
            
        return await cls.create(session, **kwargs)