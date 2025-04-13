from app.dao.base import BaseDAO
from app.hospital_staff.models import HospitalStaff
from app.database import async_session_maker
from sqlalchemy import select, text
from sqlalchemy.orm import joinedload
from typing import Any, Dict, List, Optional

from app.common.enums import BloodType


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
        

    @classmethod
    async def find_staff_by_performance(
        cls,
        min_requests: int = 5,
        min_fulfillment_rate: float = 70.0,
        months: int = 6,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find hospital staff by their blood request fulfillment rate.
        
        Args:
            min_requests: Minimum number of requests created
            min_fulfillment_rate: Minimum fulfillment rate percentage
            months: Look back period in months
            limit: Maximum number of results
        """
        async with async_session_maker() as session:
            query = text("""
            WITH staff_stats AS (
                SELECT
                    hs.id AS staff_id,
                    u.id AS user_id,
                    u.first_name,
                    u.last_name,
                    u.email,
                    hs.role,
                    h.id AS hospital_id,
                    h.name AS hospital_name,
                    COUNT(br.id) AS total_requests,
                    SUM(CASE WHEN br.status = 'FULFILLED' THEN 1 ELSE 0 END) AS fulfilled_requests,
                    CASE 
                        WHEN COUNT(br.id) > 0 THEN
                            ROUND((SUM(CASE WHEN br.status = 'FULFILLED' THEN 1 ELSE 0 END)::numeric / 
                            COUNT(br.id)::numeric) * 100, 2)
                        ELSE 0
                    END AS fulfillment_rate
                FROM
                    hospital_staff hs
                JOIN
                    users u ON hs.user_id = u.id
                JOIN
                    hospitals h ON hs.hospital_id = h.id
                JOIN
                    blood_requests br ON hs.id = br.staff_id
                WHERE
                    br.created_at > NOW() - (:months * interval '1 month')
                GROUP BY
                    hs.id, u.id, u.first_name, u.last_name, u.email, hs.role, h.id, h.name
                HAVING
                    COUNT(br.id) >= :min_requests
            )
            SELECT
                staff_id,
                user_id,
                first_name,
                last_name,
                email,
                role,
                hospital_id,
                hospital_name,
                total_requests,
                fulfilled_requests,
                fulfillment_rate,
                (SELECT COUNT(DISTINCT br.blood_type) 
                FROM blood_requests br 
                WHERE br.staff_id = ss.staff_id 
                AND br.created_at > NOW() - INTERVAL ':months months') AS blood_type_count,
                (SELECT STRING_AGG(DISTINCT br.blood_type::text, ', ')
                FROM blood_requests br 
                WHERE br.staff_id = ss.staff_id 
                AND br.created_at > NOW() - (:months * interval '1 month')) AS blood_types
            FROM
                staff_stats ss
            WHERE
                fulfillment_rate >= :min_fulfillment_rate
            ORDER BY
                fulfillment_rate DESC,
                total_requests DESC
            LIMIT :limit
            """)
            
            result = await session.execute(
                query, 
                {
                    "min_requests": min_requests,
                    "min_fulfillment_rate": min_fulfillment_rate,
                    "months": months, 
                    "limit": limit
                }
            )
            
            staff_list = []
            for row in result.mappings():
                staff_dict = dict(row)
                if staff_dict.get('blood_types'):
                    blood_types_list = staff_dict['blood_types'].split(', ')
                    converted_types = []
                    for bt_name in blood_types_list:
                        for bt in BloodType:
                            if bt.name == bt_name:
                                converted_types.append(bt.value)
                                break
                    staff_dict['blood_types'] = ', '.join(converted_types)
                
                staff_list.append(staff_dict)
                    
            return staff_list