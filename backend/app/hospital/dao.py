from app.dao.base import BaseDAO
from app.hospital.models import Hospital
from app.database import async_session_maker
from sqlalchemy import func, select, or_, text
from app.common.enums import DonationStatus, RequestStatus
from typing import List, Optional, Tuple, Dict, Any
from app.hospital_staff.models import HospitalStaff
from app.blood_request.models import BloodRequest
from sqlalchemy import func, select


class HospitalDAO(BaseDAO):
    model = Hospital

    @classmethod
    async def find_paginated(cls, page: int = 1, limit: int = 10, search: Optional[str] = None) -> Tuple[List[Hospital], int]:
        """
        Find hospitals with pagination and optional search
        
        Args:
            page: Page number (1-indexed)
            limit: Number of items per page
            search: Optional search term for hospital name, city, or region
            
        Returns:
            Tuple of (list of hospitals, total count)
        """
        offset = (page - 1) * limit
        
        async with async_session_maker() as session:
            # Base query
            query = select(cls.model)
            count_query = select(func.count(cls.model.id))
            
            # Apply search filter if provided
            if search:
                search_pattern = f"%{search}%"
                search_filter = or_(
                    cls.model.name.ilike(search_pattern),
                    cls.model.city.ilike(search_pattern),
                    cls.model.region.ilike(search_pattern)
                )
                query = query.where(search_filter)
                count_query = count_query.where(search_filter)
            
            # Get total count
            total_count = await session.scalar(count_query)
            
            # Get paginated results
            query = query.order_by(cls.model.name).offset(offset).limit(limit)
            result = await session.execute(query)
            hospitals = result.scalars().all()
            
            return hospitals, total_count

    @classmethod
    async def get_hospital_stats(cls, hospital_id: int) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific hospital
        
        Args:
            hospital_id: ID of the hospital
            
        Returns:
            Dictionary with statistics or None if hospital not found
        """
        async with async_session_maker() as session:
            # Check if hospital exists
            hospital = await session.get(cls.model, hospital_id)
            if not hospital:
                return None
                
            # Import models here to avoid circular imports
            from app.donation.models import Donation
            from app.hospital_staff.models import HospitalStaff
            from app.blood_request.models import BloodRequest
            
            # Get staff count
            staff_count_query = select(func.count(HospitalStaff.id)).where(
                HospitalStaff.hospital_id == hospital_id
            )
            staff_count = await session.scalar(staff_count_query) or 0
            
            # Get blood requests counts
            blood_requests_query = select(func.count(BloodRequest.id)).where(
                BloodRequest.hospital_id == hospital_id
            )
            blood_requests_count = await session.scalar(blood_requests_query) or 0
            
            # Get active requests count
            active_requests_query = select(func.count(BloodRequest.id)).where(
                BloodRequest.hospital_id == hospital_id,
                BloodRequest.status == RequestStatus.PENDING
            )
            active_requests = await session.scalar(active_requests_query) or 0
            
            # Get scheduled donations count
            scheduled_donations_query = select(func.count(Donation.id)).where(
                Donation.hospital_id == hospital_id,
                Donation.status == DonationStatus.SCHEDULED
            )
            scheduled_donations = await session.scalar(scheduled_donations_query) or 0
            
            # Get completed donations count
            completed_donations_query = select(func.count(Donation.id)).where(
                Donation.hospital_id == hospital_id,
                Donation.status == DonationStatus.COMPLETED
            )
            completed_donations = await session.scalar(completed_donations_query) or 0
            
            return {
                "id": hospital_id,
                "name": hospital.name,
                "staff_count": staff_count,
                "blood_requests_count": blood_requests_count,
                "active_requests": active_requests,
                "scheduled_donations": scheduled_donations,
                "completed_donations": completed_donations
            }

    @classmethod
    async def delete(cls, id: int) -> bool:
        """
        Delete a hospital by ID
        
        Args:
            id: ID of the hospital to delete
            
        Returns:
            True if successful, False otherwise
        """
        async with async_session_maker() as session:
            async with session.begin():
                hospital = await session.get(cls.model, id)
                if not hospital:
                    return False
                
                await session.delete(hospital)
                return True

    @classmethod
    async def update(cls, id: int, **values) -> Optional[Hospital]:
        """
        Update a hospital by ID
        
        Args:
            id: ID of the hospital to update
            **values: Values to update
            
        Returns:
            Updated hospital or None if not found
        """
        async with async_session_maker() as session:
            hospital = await session.get(cls.model, id)
            if not hospital:
                return None
            
            for key, value in values.items():
                if value is not None:  
                    setattr(hospital, key, value)
            
            await session.commit()
            
            await session.refresh(hospital)
            return hospital
            
    @classmethod
    async def can_be_deleted(cls, hospital_id: int) -> bool:
        """
        Check if a hospital can be safely deleted
        
        Args:
            hospital_id: ID of the hospital
            
        Returns:
            True if hospital can be deleted, False otherwise
        """
        async with async_session_maker() as session:
            
            staff_count_query = select(func.count(HospitalStaff.id)).where(
                HospitalStaff.hospital_id == hospital_id
            )
            staff_count = await session.scalar(staff_count_query) or 0
            if staff_count > 0:
                return False
            
            requests_count_query = select(func.count(BloodRequest.id)).where(
                BloodRequest.hospital_id == hospital_id
            )
            requests_count = await session.scalar(requests_count_query) or 0
            if requests_count > 0:
                return False
            
            return True
        

    @classmethod
    async def find_hospitals_with_identical_needs(cls, reference_hospital_id, time_period_days=30, min_shortage_percent=25.0, limit=50):
        async with async_session_maker() as session:
            query = text("""
            WITH reference_hospital_needs AS (
                -- Calculate blood type shortages for reference hospital
                SELECT 
                    h.id AS hospital_id,
                    h.name AS hospital_name,
                    br.blood_type,
                    COUNT(DISTINCT br.id) AS request_count,
                    SUM(br.amount_needed_ml) AS total_needed_ml,
                    SUM(COALESCE(d.collected_ml, 0)) AS total_collected_ml,
                    SUM(br.amount_needed_ml) - SUM(COALESCE(d.collected_ml, 0)) AS shortage_ml,
                    (SUM(br.amount_needed_ml) - SUM(COALESCE(d.collected_ml, 0))) * 100.0 / 
                        NULLIF(SUM(br.amount_needed_ml), 0) AS shortage_percent
                FROM 
                    hospitals h
                JOIN 
                    blood_requests br ON h.id = br.hospital_id
                LEFT JOIN (
                    -- Subquery to get sum of collected blood by request
                    SELECT 
                        blood_request_id,
                        SUM(blood_amount_ml) AS collected_ml
                    FROM 
                        donations
                    WHERE 
                        status = 'COMPLETED'
                    GROUP BY 
                        blood_request_id
                ) d ON br.id = d.blood_request_id
                WHERE 
                    h.id = :reference_hospital_id
                    AND br.status IN ('PENDING', 'APPROVED')
                    AND br.request_date >= CURRENT_DATE - (:time_period_days * INTERVAL '1 day')
                GROUP BY 
                    h.id, h.name, br.blood_type
                HAVING 
                    (SUM(br.amount_needed_ml) - SUM(COALESCE(d.collected_ml, 0))) * 100.0 / 
                    NULLIF(SUM(br.amount_needed_ml), 0) >= :min_shortage_percent
                ORDER BY 
                    br.blood_type
            ),
            other_hospitals_needs AS (
                -- Calculate blood type shortages for all other hospitals
                SELECT 
                    h.id AS hospital_id,
                    h.name AS hospital_name,
                    h.city,
                    h.region,
                    br.blood_type,
                    COUNT(DISTINCT br.id) AS request_count,
                    SUM(br.amount_needed_ml) AS total_needed_ml,
                    SUM(COALESCE(d.collected_ml, 0)) AS total_collected_ml,
                    SUM(br.amount_needed_ml) - SUM(COALESCE(d.collected_ml, 0)) AS shortage_ml,
                    (SUM(br.amount_needed_ml) - SUM(COALESCE(d.collected_ml, 0))) * 100.0 / 
                        NULLIF(SUM(br.amount_needed_ml), 0) AS shortage_percent
                FROM 
                    hospitals h
                JOIN 
                    blood_requests br ON h.id = br.hospital_id
                LEFT JOIN (
                    -- Subquery to get sum of collected blood by request
                    SELECT 
                        blood_request_id,
                        SUM(blood_amount_ml) AS collected_ml
                    FROM 
                        donations
                    WHERE 
                        status = 'COMPLETED'
                    GROUP BY 
                        blood_request_id
                ) d ON br.id = d.blood_request_id
                WHERE 
                    h.id != :reference_hospital_id
                    AND br.status IN ('PENDING', 'APPROVED')
                    AND br.request_date >= CURRENT_DATE - (:time_period_days * INTERVAL '1 day')
                GROUP BY 
                    h.id, h.name, h.city, h.region, br.blood_type
                HAVING
                    (SUM(br.amount_needed_ml) - SUM(COALESCE(d.collected_ml, 0))) * 100.0 / 
                    NULLIF(SUM(br.amount_needed_ml), 0) >= :min_shortage_percent
            ),
            ref_blood_types AS (
                -- Get the distinct set of blood types needed by reference hospital
                SELECT ARRAY_AGG(blood_type ORDER BY blood_type) AS blood_types
                FROM reference_hospital_needs
            ),
            hospital_blood_types AS (
                -- Get the set of blood types needed by each other hospital
                SELECT 
                    hospital_id,
                    hospital_name,
                    city,
                    region,
                    ARRAY_AGG(blood_type ORDER BY blood_type) AS blood_types,
                    STRING_AGG(blood_type::text, ', ' ORDER BY blood_type) AS blood_types_str
                FROM 
                    other_hospitals_needs
                GROUP BY 
                    hospital_id, hospital_name, city, region
            ),
            reference_details AS (
                -- Get reference hospital details
                SELECT 
                    h.id,
                    h.name,
                    h.city,
                    h.region,
                    (SELECT STRING_AGG(blood_type::text, ', ' ORDER BY blood_type) 
                     FROM reference_hospital_needs) AS blood_types_str
                FROM 
                    hospitals h
                WHERE 
                    h.id = :reference_hospital_id
            )
            -- Final selection: hospitals with identical blood type patterns
            SELECT 
                hbt.hospital_id,
                hbt.hospital_name,
                hbt.city,
                hbt.region,
                hbt.blood_types_str,
                array_length(hbt.blood_types, 1) AS blood_type_count,
                rd.name AS reference_hospital_name,
                rd.city AS reference_city,
                rd.region AS reference_region,
                rd.blood_types_str AS reference_blood_types
            FROM 
                hospital_blood_types hbt
            CROSS JOIN 
                ref_blood_types rbt
            CROSS JOIN
                reference_details rd
            WHERE 
                hbt.blood_types = rbt.blood_types
            ORDER BY 
                hbt.city, hbt.hospital_name
            LIMIT :limit
            """)
            

            result = await session.execute(
                query,
                {
                    "reference_hospital_id": reference_hospital_id,
                    "time_period_days": time_period_days,
                    "min_shortage_percent": min_shortage_percent,
                    "limit": limit
                }
            )
            
            return [dict(row) for row in result.mappings()]
        

    @classmethod
    async def get_all_hospitals(cls, limit=100):
        """Get all hospitals with an optional limit"""
        async with async_session_maker() as session:
            query = select(cls.model).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()
        
    @classmethod
    async def get_unique_regions(cls) -> List[str]:
        """
        Get a list of all unique regions where hospitals are located.
        
        Returns:
            List of unique region names sorted alphabetically
        """
        async with async_session_maker() as session:
            query = select(cls.model.region).distinct().order_by(cls.model.region)
            result = await session.execute(query)
            regions = result.scalars().all()
            
            # Filter out None values
            return [region for region in regions if region]
        

    @classmethod
    async def find_hospitals_with_similar_blood_request_patterns(
        cls, 
        min_similarity_percent: float = 50.0,
        min_request_count: int = 3,
        time_period_months: int = 24,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Знаходить пари лікарень з подібними патернами запитів на групи крові.
        """
        async with async_session_maker() as session:
            query = text(f"""
            WITH blood_requests_by_hospital AS (
                -- Запити на кров по кожній лікарні 
                SELECT 
                    h.id AS hospital_id,
                    h.name AS hospital_name,
                    h.city,
                    h.region,
                    br.blood_type,
                    COUNT(*) AS request_count
                FROM 
                    hospitals h
                JOIN 
                    blood_requests br ON h.id = br.hospital_id
                WHERE 
                    br.created_at >= CURRENT_DATE - (:time_period_months * INTERVAL '1 month')
                GROUP BY 
                    h.id, h.name, h.city, h.region, br.blood_type
            ),
            hospital_blood_types AS (
                -- Агрегація груп крові по лікарням
                SELECT 
                    hospital_id,
                    hospital_name,
                    city,
                    region,
                    ARRAY_AGG(blood_type ORDER BY blood_type) AS blood_types,
                    STRING_AGG(blood_type::text, ', ' ORDER BY blood_type::text) AS blood_types_str,
                    SUM(request_count) AS total_requests
                FROM 
                    blood_requests_by_hospital
                GROUP BY 
                    hospital_id, hospital_name, city, region
                HAVING 
                    SUM(request_count) >= :min_request_count
            ),
            hospital_pairs AS (
                -- Формуємо всі можливі пари лікарень
                SELECT 
                    h1.hospital_id AS hospital1_id,
                    h1.hospital_name AS hospital1_name,
                    h1.city AS hospital1_city,
                    h1.region AS hospital1_region,
                    h1.blood_types AS hospital1_blood_types,
                    h1.blood_types_str AS hospital1_blood_types_str,
                    h1.total_requests AS hospital1_requests,
                    
                    h2.hospital_id AS hospital2_id,
                    h2.hospital_name AS hospital2_name,
                    h2.city AS hospital2_city,
                    h2.region AS hospital2_region,
                    h2.blood_types AS hospital2_blood_types,
                    h2.blood_types_str AS hospital2_blood_types_str,
                    h2.total_requests AS hospital2_requests,
                    
                    -- Спільні групи крові (перетин)
                    (
                        SELECT COUNT(*) FROM (
                            SELECT UNNEST(h1.blood_types)
                            INTERSECT
                            SELECT UNNEST(h2.blood_types)
                        ) AS common
                    ) AS common_blood_types_count,
                    
                    -- Всі унікальні групи крові (об'єднання)
                    (
                        SELECT COUNT(*) FROM (
                            SELECT UNNEST(h1.blood_types)
                            UNION
                            SELECT UNNEST(h2.blood_types)
                        ) AS all_types  -- Змінено з "all" на "all_types"
                    ) AS total_blood_types_count,
                    
                    -- Географічні відносини
                    CASE
                        WHEN h1.region = h2.region AND h1.city = h2.city THEN 'Одне місто'
                        WHEN h1.region = h2.region THEN 'Один регіон'
                        ELSE 'Різні регіони'
                    END AS geographical_relation
                FROM 
                    hospital_blood_types h1
                JOIN 
                    hospital_blood_types h2 ON h1.hospital_id < h2.hospital_id
            )
            SELECT 
                *,
                -- Розрахунок відсотка схожості
                ROUND((common_blood_types_count * 100.0 / NULLIF(total_blood_types_count, 0)), 1) AS similarity_percent,
                
                -- Текстовий перелік спільних груп крові
                (
                    SELECT STRING_AGG(bt::text, ', ' ORDER BY bt::text) 
                    FROM (
                        SELECT UNNEST(hospital1_blood_types) AS bt
                        INTERSECT
                        SELECT UNNEST(hospital2_blood_types) AS bt
                    ) AS common
                ) AS common_blood_types,
                
                -- Різниця груп крові (є в першій, немає в другій)
                (
                    SELECT STRING_AGG(bt::text, ', ' ORDER BY bt::text)
                    FROM (
                        SELECT UNNEST(hospital1_blood_types) AS bt
                        EXCEPT
                        SELECT UNNEST(hospital2_blood_types) AS bt
                    ) AS diff
                ) AS hospital1_unique_types,
                
                -- Різниця груп крові (є в другій, немає в першій)
                (
                    SELECT STRING_AGG(bt::text, ', ' ORDER BY bt::text)
                    FROM (
                        SELECT UNNEST(hospital2_blood_types) AS bt
                        EXCEPT
                        SELECT UNNEST(hospital1_blood_types) AS bt
                    ) AS diff
                ) AS hospital2_unique_types,
                
                -- Опис рівня схожості
                CASE 
                    WHEN (common_blood_types_count * 100.0 / NULLIF(total_blood_types_count, 0)) >= 90 THEN 'Надзвичайно висока'
                    WHEN (common_blood_types_count * 100.0 / NULLIF(total_blood_types_count, 0)) >= 75 THEN 'Дуже висока'
                    WHEN (common_blood_types_count * 100.0 / NULLIF(total_blood_types_count, 0)) >= 60 THEN 'Висока'
                    ELSE 'Середня'
                END AS similarity_level
            FROM 
                hospital_pairs
            WHERE 
                -- Фільтрація по мінімальному рівню схожості
                (common_blood_types_count * 100.0 / NULLIF(total_blood_types_count, 0)) >= :min_similarity_percent
            ORDER BY 
                similarity_percent DESC,
                common_blood_types_count DESC,
                hospital1_requests + hospital2_requests DESC
            LIMIT :limit
            """)
            
            result = await session.execute(
                query, 
                {
                    "min_similarity_percent": min_similarity_percent,
                    "min_request_count": min_request_count,
                    "time_period_months": time_period_months,
                    "limit": limit
                }
            )
            
            return [dict(row) for row in result.mappings()]