from app.dao.base import BaseDAO
from app.hospital.models import Hospital
from app.database import async_session_maker
from sqlalchemy import func, select, or_
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