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
        

    @classmethod
    async def find_staff_with_matching_request_patterns(
        cls,
        min_blood_types: int = 2,
        min_similarity_percent: float = 90.0,
        time_period_months: int = 6,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find pairs of hospital staff who have created the same pattern of blood type requests.
        """
        async with async_session_maker() as session:
            query = text("""
            WITH staff_request_patterns AS (
                -- Calculate the blood type request patterns for each staff member
                SELECT 
                    hs.id AS staff_id,
                    u.id AS user_id,
                    u.first_name,
                    u.last_name,
                    u.email,
                    hs.role,
                    h.id AS hospital_id,
                    h.name AS hospital_name,
                    h.city,
                    h.region,
                    COUNT(DISTINCT br.blood_type) AS blood_type_count,
                    ARRAY_AGG(DISTINCT br.blood_type ORDER BY br.blood_type) AS blood_types,
                    STRING_AGG(DISTINCT br.blood_type::text, ', ' ORDER BY br.blood_type::text) AS blood_types_str,
                    COUNT(br.id) AS request_count,
                    SUM(CASE WHEN br.status = 'FULFILLED' THEN 1 ELSE 0 END) AS fulfilled_count,
                    AVG(br.urgency_level) AS avg_urgency
                FROM 
                    hospital_staff hs
                JOIN 
                    users u ON hs.user_id = u.id
                JOIN 
                    hospitals h ON hs.hospital_id = h.id
                JOIN 
                    blood_requests br ON hs.id = br.staff_id
                WHERE 
                    br.request_date >= CURRENT_DATE - (:months * INTERVAL '1 month')
                GROUP BY 
                    hs.id, u.id, u.first_name, u.last_name, u.email, hs.role, h.id, h.name, h.city, h.region
                HAVING 
                    COUNT(DISTINCT br.blood_type) >= :min_blood_types
            ),
            staff_pairs AS (
                -- Generate all possible pairs of staff with matching request patterns
                SELECT 
                    a.staff_id AS staff_id_1,
                    a.user_id AS user_id_1,
                    a.first_name AS first_name_1,
                    a.last_name AS last_name_1,
                    a.role AS role_1,
                    a.hospital_id AS hospital_id_1,
                    a.hospital_name AS hospital_name_1,
                    a.city AS city_1,
                    a.region AS region_1,
                    a.blood_types AS blood_types_1,
                    a.blood_types_str AS blood_types_str_1,
                    a.request_count AS request_count_1,
                    a.fulfilled_count AS fulfilled_count_1,
                    a.avg_urgency AS avg_urgency_1,
                    
                    b.staff_id AS staff_id_2,
                    b.user_id AS user_id_2,
                    b.first_name AS first_name_2,
                    b.last_name AS last_name_2,
                    b.role AS role_2,
                    b.hospital_id AS hospital_id_2,
                    b.hospital_name AS hospital_name_2,
                    b.city AS city_2,
                    b.region AS region_2,
                    b.blood_types AS blood_types_2,
                    b.blood_types_str AS blood_types_str_2,
                    b.request_count AS request_count_2,
                    b.fulfilled_count AS fulfilled_count_2,
                    b.avg_urgency AS avg_urgency_2,
                    
                    -- Calculate similarity metrics
                    CASE 
                        WHEN a.blood_types = b.blood_types THEN 100.0
                        ELSE
                            -- Calculate Jaccard similarity
                            (
                                (SELECT COUNT(*) FROM 
                                    (SELECT UNNEST(a.blood_types) INTERSECT SELECT UNNEST(b.blood_types)) as intersection
                                ) * 100.0 / 
                                (SELECT COUNT(*) FROM 
                                    (SELECT UNNEST(a.blood_types) UNION SELECT UNNEST(b.blood_types)) as union_set
                                )
                            )
                    END AS blood_type_similarity,
                    
                    ABS(a.avg_urgency - b.avg_urgency) AS urgency_diff,
                    ABS(
                        (a.fulfilled_count * 100.0 / NULLIF(a.request_count, 0)) - 
                        (b.fulfilled_count * 100.0 / NULLIF(b.request_count, 0))
                    ) AS fulfillment_rate_diff,
                    
                    (SELECT COUNT(*) FROM UNNEST(a.blood_types) bt) AS blood_type_count,
                    (
                        CASE 
                            WHEN a.hospital_id = b.hospital_id THEN 'Same Hospital'
                            WHEN a.region = b.region THEN 'Same Region'
                            ELSE 'Different Regions'
                        END
                    ) AS location_relation
                FROM 
                    staff_request_patterns a
                JOIN 
                    staff_request_patterns b ON a.staff_id < b.staff_id
                WHERE
                    -- Only include pairs with high blood type similarity
                    CASE 
                        WHEN a.blood_types = b.blood_types THEN 100.0
                        ELSE
                            (
                                (SELECT COUNT(*) FROM 
                                    (SELECT UNNEST(a.blood_types) INTERSECT SELECT UNNEST(b.blood_types)) as intersection
                                ) * 100.0 / 
                                (SELECT COUNT(*) FROM 
                                    (SELECT UNNEST(a.blood_types) UNION SELECT UNNEST(b.blood_types)) as union_set
                                )
                            )
                    END >= :min_similarity
            )
            -- Final selection
            SELECT
                sp.*,
                CASE 
                    WHEN blood_type_similarity = 100.0 THEN 'Identical'
                    WHEN blood_type_similarity >= 90.0 THEN 'Very Similar'
                    WHEN blood_type_similarity >= 75.0 THEN 'Similar'
                    ELSE 'Partial Match'
                END AS similarity_category,
                (
                    blood_type_similarity - 
                    LEAST(urgency_diff * 5.0, 20.0) - 
                    LEAST(fulfillment_rate_diff * 0.25, 15.0)
                ) AS overall_similarity_score
            FROM 
                staff_pairs sp
            ORDER BY 
                blood_type_similarity DESC,
                overall_similarity_score DESC,
                blood_type_count DESC
            LIMIT :limit
            """)
            
            result = await session.execute(
                query, 
                {
                    "min_blood_types": min_blood_types,
                    "min_similarity": min_similarity_percent,
                    "months": time_period_months,
                    "limit": limit
                }
            )
            
            return [dict(row) for row in result.mappings()]