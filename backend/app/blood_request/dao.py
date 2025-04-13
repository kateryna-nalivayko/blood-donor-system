from app.dao.base import BaseDAO
from app.blood_request.models import BloodRequest
from app.database import async_session_maker
from sqlalchemy import select, func, and_, text
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.common.enums import BloodType, RequestStatus
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import selectinload
from app.database import async_session_maker
from app.donation.models import Donation
from app.donor.models import Donor


class BloodRequestDAO(BaseDAO):
    model = BloodRequest

    @classmethod
    async def add(cls, **values):
        async with async_session_maker() as session:
            instance = cls.model(**values)
            session.add(instance)
            await session.commit()
            
            await session.refresh(instance)
            
            query = select(cls.model).options(
                selectinload(cls.model.donations)
            ).filter(cls.model.id == instance.id)
            
            result = await session.execute(query)
            return result.scalar_one()
    

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        """Override to eager load donations relationship"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                selectinload(cls.model.donations)
            ).filter_by(**filter_by)
            
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @classmethod
    async def find_all(
        cls, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None,
        order_by: Optional[List] = None,
        **filter_by
    ):
        """Find all blood requests with optional filtering, pagination and ordering"""
        async with async_session_maker() as session:
            stmt = select(cls.model).options(
                selectinload(cls.model.donations)
            )
            
            # Apply filters
            for field, value in filter_by.items():
                if hasattr(cls.model, field):
                    stmt = stmt.filter(getattr(cls.model, field) == value)
            
            # Apply ordering
            if order_by:
                stmt = stmt.order_by(*order_by)
            
            # Apply pagination
            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)
                
            result = await session.execute(stmt)
            return result.scalars().all()
    
    @classmethod
    async def update(cls, request_id, **values):
        """Update a blood request by ID and return the updated instance with relationships loaded"""
        async with async_session_maker() as session:
            # Get the blood request with ID
            stmt = select(cls.model).options(
                selectinload(cls.model.donations),
                joinedload(cls.model.staff),
                joinedload(cls.model.hospital)
            ).where(cls.model.id == request_id)
            
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()
            
            if not instance:
                return None
            
            # Update the instance with the provided values
            for key, value in values.items():
                setattr(instance, key, value)
            
            # Commit the changes
            await session.commit()
            
            # Refresh the instance with the updated values and ensure relationships are loaded
            await session.refresh(instance, ["donations", "staff", "hospital"])
            
            # Access computed properties to ensure they're calculated with relationships loaded
            _ = instance.collected_amount_ml
            _ = instance.fulfillment_percentage
            _ = instance.days_until_needed
            _ = instance.is_fulfilled
            
            return instance
    
    @classmethod
    async def delete(cls, **filter_by):
        """Delete blood requests by filter criteria"""
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            instances = result.scalars().all()
            
            for instance in instances:
                await session.delete(instance)
            
            await session.commit()
            return len(instances)
    
    @classmethod
    async def find_by_min_urgency(cls, urgency_min: int, **filters):
        """Find requests with minimum urgency level"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                selectinload(cls.model.donations)
            ).filter(cls.model.urgency_level >= urgency_min)
            
            for field, value in filters.items():
                query = query.filter(getattr(cls.model, field) == value)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    @classmethod
    async def get_summary(cls, hospital_id: Optional[int] = None) -> Dict[str, Any]:
        """Get statistical summary of blood requests"""
        async with async_session_maker() as session:
            filters = []
            if hospital_id:
                filters.append(cls.model.hospital_id == hospital_id)
            
            total_query = select(func.count()).select_from(cls.model)
            if filters:
                total_query = total_query.where(and_(*filters))
            total_result = await session.execute(total_query)
            total_requests = total_result.scalar() or 0
            
            pending_query = select(func.count()).select_from(cls.model).where(
                cls.model.status == "pending",
                *filters
            )
            pending_result = await session.execute(pending_query)
            pending_requests = pending_result.scalar() or 0
            
            fulfilled_query = select(func.count()).select_from(cls.model).where(
                cls.model.status == "fulfilled",
                *filters
            )
            fulfilled_result = await session.execute(fulfilled_query)
            fulfilled_requests = fulfilled_result.scalar() or 0
            
            urgent_query = select(func.count()).select_from(cls.model).where(
                cls.model.urgency_level >= 4,
                *filters
            )
            urgent_result = await session.execute(urgent_query)
            urgent_requests = urgent_result.scalar() or 0
            
            blood_type_query = select(
                cls.model.blood_type,
                func.count().label("count")
            ).group_by(cls.model.blood_type)
            if filters:
                blood_type_query = blood_type_query.where(and_(*filters))
            blood_type_result = await session.execute(blood_type_query)
            by_blood_type = {row[0]: row[1] for row in blood_type_result}
            
            return {
                "total_requests": total_requests,
                "pending_requests": pending_requests,
                "fulfilled_requests": fulfilled_requests,
                "urgent_requests": urgent_requests,
                "by_blood_type": by_blood_type
            }
        
    @classmethod
    async def find_with_properties(cls, **filter_by):
        """Find blood requests with eager loading and compute properties"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                selectinload(cls.model.donations)
            ).filter_by(**filter_by)
            
            result = await session.execute(query)
            instances = result.scalars().all()
            
            for instance in instances:
                _ = instance.collected_amount_ml
                _ = instance.fulfillment_percentage
                _ = instance.days_until_needed
                _ = instance.is_fulfilled
                
            return instances
    
    @classmethod
    async def count(cls, **filter_by) -> int:
        """Count blood requests with optional filtering"""
        async with async_session_maker() as session:
            stmt = select(func.count()).select_from(cls.model)
            
            # Apply filters
            for field, value in filter_by.items():
                if hasattr(cls.model, field):
                    stmt = stmt.where(getattr(cls.model, field) == value)
                    
            result = await session.execute(stmt)
            return result.scalar() or 0
    
    @classmethod
    async def count_by_min_urgency(cls, urgency_min: int, **filter_by) -> int:
        """Count blood requests with minimum urgency level and optional filtering"""
        async with async_session_maker() as session:
            stmt = select(func.count()).select_from(cls.model)
            
            # Add urgency filter
            stmt = stmt.where(cls.model.urgency_level >= urgency_min)
            
            # Apply additional filters
            for field, value in filter_by.items():
                if hasattr(cls.model, field):
                    stmt = stmt.where(getattr(cls.model, field) == value)
                    
            result = await session.execute(stmt)
            return result.scalar() or 0
        

    @classmethod
    async def find_one_with_staff(cls, **filter_by):
        """Find one blood request with all relationships eager loaded"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                selectinload(cls.model.donations),
                joinedload(cls.model.staff),
                joinedload(cls.model.hospital)
            ).filter_by(**filter_by)
            
            result = await session.execute(query)
            return result.scalar_one_or_none()
        
    @classmethod
    async def find_one_with_all_relations(cls, request_id: int):
        """Find blood request with all nested relationships for detail page"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                selectinload(cls.model.donations).selectinload(Donation.donor).selectinload(Donor.user),
                joinedload(cls.model.staff),
                joinedload(cls.model.hospital)
            ).where(cls.model.id == request_id)
            
            result = await session.execute(query)
            return result.scalar_one_or_none()
        
    @classmethod
    async def find_hospitals_with_shortages(
        cls,
        blood_type: str,
        fulfillment_percentage: float = 50.0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find hospitals with blood requests of a specific type that don't have enough donations.
        
        Args:
            blood_type: Blood type to filter by
            fulfillment_percentage: Maximum fulfillment percentage to be considered a shortage
            limit: Maximum number of results to return
            
        Returns:
            List of hospitals with blood shortages
        """
        blood_type_enum = None
        for bt in BloodType:
            if bt.value == blood_type:
                blood_type_enum = bt.name
                break
                
        if not blood_type_enum:
            return []
        
        async with async_session_maker() as session:
            query = text("""
            WITH request_donations AS (
                SELECT 
                    br.id AS request_id,
                    COALESCE(SUM(don.blood_amount_ml), 0) AS total_donated
                FROM 
                    blood_requests br
                LEFT JOIN 
                    donations don ON br.id = don.blood_request_id AND don.status = 'COMPLETED'
                WHERE 
                    br.blood_type = :blood_type
                    AND br.status IN ('PENDING', 'APPROVED')
                GROUP BY 
                    br.id
            )
            SELECT 
                h.id AS hospital_id,
                h.name AS hospital_name,
                h.city,
                br.id AS request_id,
                br.blood_type,
                br.amount_needed_ml,
                COALESCE(rd.total_donated, 0) AS collected_ml,
                (br.amount_needed_ml - COALESCE(rd.total_donated, 0)) AS shortage_ml,
                COALESCE((rd.total_donated * 100.0 / NULLIF(br.amount_needed_ml, 0)), 0) AS fulfillment_percentage,
                br.needed_by_date::date AS needed_by_date,
                br.urgency_level
            FROM 
                hospitals h
            JOIN 
                blood_requests br ON h.id = br.hospital_id
            JOIN
                request_donations rd ON br.id = rd.request_id
            WHERE 
                br.blood_type = :blood_type
                AND br.status IN ('PENDING', 'APPROVED')
                AND COALESCE((rd.total_donated * 100.0 / NULLIF(br.amount_needed_ml, 0)), 0) < :fulfillment_percentage
            ORDER BY 
                br.urgency_level DESC,
                br.needed_by_date ASC,
                fulfillment_percentage ASC
            LIMIT :limit
            """)
            
            result = await session.execute(
                query, 
                {
                    "blood_type": blood_type_enum, 
                    "fulfillment_percentage": fulfillment_percentage,
                    "limit": limit
                }
            )
            
            shortages = []
            for row in result.mappings():  
                shortage_dict = dict(row)
                for bt in BloodType:
                    if bt.name == shortage_dict['blood_type']:
                        shortage_dict['blood_type'] = bt.value
                        break
                
                shortages.append(shortage_dict)
                    
            return shortages
        

    @classmethod
    async def find_high_volume_requests(
        cls,
        min_volume_ml: int = 1000,
        min_urgency: int = 3,
        days: int = 30,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find high-volume blood requests that meet minimum urgency level.
        
        Args:
            min_volume_ml: Minimum volume of blood needed
            min_urgency: Minimum urgency level (1-5)
            days: Look ahead period in days
            limit: Maximum number of results
        """
        async with async_session_maker() as session:
            query = text("""
            SELECT 
                br.id AS request_id,
                h.id AS hospital_id,
                h.name AS hospital_name,
                h.city,
                h.region,
                br.blood_type,
                br.amount_needed_ml,
                br.urgency_level,
                COALESCE(SUM(d.blood_amount_ml), 0) AS collected_ml,
                br.amount_needed_ml - COALESCE(SUM(d.blood_amount_ml), 0) AS remaining_ml,
                br.needed_by_date::date AS needed_by_date,
                CURRENT_DATE + (:days * interval '1 day') AS cutoff_date,
                u.first_name || ' ' || u.last_name AS staff_name,
                hs.role AS staff_role
            FROM 
                blood_requests br
            JOIN 
                hospitals h ON br.hospital_id = h.id
            JOIN 
                hospital_staff hs ON br.staff_id = hs.id
            JOIN 
                users u ON hs.user_id = u.id
            LEFT JOIN 
                donations d ON br.id = d.blood_request_id AND d.status = 'COMPLETED'
            WHERE 
                br.amount_needed_ml >= :min_volume_ml
                AND br.urgency_level >= :min_urgency
                AND br.status IN ('PENDING', 'APPROVED')
                AND br.needed_by_date <= CURRENT_DATE + (:days * interval '1 day')
            GROUP BY 
                br.id, h.id, h.name, h.city, h.region, br.blood_type, 
                br.amount_needed_ml, br.urgency_level, br.needed_by_date,
                u.first_name, u.last_name, hs.role
            ORDER BY 
                br.urgency_level DESC, 
                br.needed_by_date ASC, 
                br.amount_needed_ml DESC
            LIMIT :limit
            """)
            
            result = await session.execute(
                query, 
                {
                    "min_volume_ml": min_volume_ml,
                    "min_urgency": min_urgency,
                    "days": days, 
                    "limit": limit
                }
            )
            
            requests = []
            for row in result.mappings():
                request_dict = dict(row)
                for bt in BloodType:
                    if bt.name == request_dict['blood_type']:
                        request_dict['blood_type'] = bt.value
                        break
                requests.append(request_dict)
                    
            return requests