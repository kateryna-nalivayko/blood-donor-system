from app.dao.base import BaseDAO
from app.blood_request.models import BloodRequest
from app.database import async_session_maker
from sqlalchemy import select, func, and_
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.common.enums import RequestStatus
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload


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
    async def find_all(cls, **filter_by):
        """Override to eager load donations relationship"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                selectinload(cls.model.donations)
            ).filter_by(**filter_by)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    @classmethod
    async def update(cls, id: int, **values):
        """Update a blood request by id"""
        async with async_session_maker() as session:
            instance = await session.get(cls.model, id)
            
            if not instance:
                return None
                
            for key, value in values.items():
                setattr(instance, key, value)
            
            await session.commit()
            await session.refresh(instance)
            
            await session.refresh(instance, ["donations"])
            
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