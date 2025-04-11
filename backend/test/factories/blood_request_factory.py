import random
from datetime import datetime, timedelta
from app.blood_request.models import BloodRequest
from app.common.enums import BloodType, RequestStatus
from .base_factory import BaseFactory, fake
from .hospital_factory import HospitalFactory
from .hospital_staff_factory import HospitalStaffFactory

class BloodRequestFactory(BaseFactory):
    model = BloodRequest
    
    @classmethod
    def _get_defaults(cls):
        """Generate default blood request data"""
        request_date = datetime.now() - timedelta(days=random.randint(0, 30))
        needed_by_date = request_date + timedelta(days=random.randint(1, 14))
        
        return {
            "blood_type": random.choice(list(BloodType)),
            "amount_needed_ml": random.randint(250, 2000),
            "patient_info": f"Patient {fake.last_name()}, {random.randint(18, 80)} years old",
            "urgency_level": random.randint(1, 5),
            "status": random.choice(list(RequestStatus)),
            "request_date": request_date,
            "needed_by_date": needed_by_date,
            "notes": fake.text(max_nb_chars=200) if random.random() > 0.5 else None
        }
    
    @classmethod
    async def create_with_relations(cls, session, **kwargs):
        """Create blood request with associated hospital and staff"""
        if "hospital_id" not in kwargs:
            hospital = await HospitalFactory.create(session)
            kwargs["hospital_id"] = hospital.id
            
        if "staff_id" not in kwargs:
            staff = await HospitalStaffFactory.create_with_relations(
                session, hospital_id=kwargs["hospital_id"]
            )
            kwargs["staff_id"] = staff.id
            
        return await cls.create(session, **kwargs)