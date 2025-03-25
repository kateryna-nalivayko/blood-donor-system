from app.dao.base import BaseDAO
from app.hospital_staff.models import HospitalStaff
from app.database import async_session_maker
from sqlalchemy import select
from typing import Optional


class HospitalStaffDAO(BaseDAO):
    model = HospitalStaff
    
    @classmethod
    async def ensure_hospital_staff_profile(cls, user_id: int, 
                                          hospital_id: int,
                                          role: str = None,
                                          department: str = None) -> HospitalStaff:
        """
        Ensure a user has a hospital staff profile, creating one if it doesn't exist.
        
        Args:
            user_id: ID of the user
            hospital_id: ID of the hospital
            role: Staff role (doctor, nurse, etc.)
            department: Department
            
        Returns:
            The existing or newly created HospitalStaff profile
        """
        async with async_session_maker() as session:
            # Check if profile already exists
            query = select(cls.model).filter_by(user_id=user_id)
            result = await session.execute(query)
            staff = result.scalar_one_or_none()
            
            if staff:
                return staff
            
            # Create new profile
            staff_data = {
                "user_id": user_id,
                "hospital_id": hospital_id
            }
            
            if role:
                staff_data["role"] = role
                
            if department:
                staff_data["department"] = department
                
            staff = cls.model(**staff_data)
            session.add(staff)
            await session.commit()
            await session.refresh(staff)
            
            return staff