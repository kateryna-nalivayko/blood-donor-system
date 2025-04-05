from app.dao.base import BaseDAO
from app.hospital_staff.models import HospitalStaff
from app.database import async_session_maker
from sqlalchemy import select
from sqlalchemy.orm import joinedload
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
        
    @classmethod
    async def update(cls, staff_id: int, **values) -> Optional[HospitalStaff]:
        """
        Update a hospital staff profile with the given values.
        
        Args:
            staff_id: ID of the hospital staff profile to update
            **values: Key-value pairs of fields to update
            
        Returns:
            Updated HospitalStaff instance or None if not found
        """
        async with async_session_maker() as session:
            staff = await session.execute(select(cls.model).filter_by(id=staff_id))
            staff = staff.scalar_one_or_none()
            
            if not staff:
                return None
            
            for key, value in values.items():
                if hasattr(staff, key):
                    setattr(staff, key, value)
            await session.commit()
            await session.refresh(staff)
            
            return staff
        
    @classmethod
    async def find_one_or_none_with_hospital(cls, **filter_by):
        """Find staff profile with hospital relationship eagerly loaded"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.hospital)
            ).filter_by(**filter_by)
            
            result = await session.execute(query)
            return result.scalar_one_or_none()