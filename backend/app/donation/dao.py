from app.dao.base import BaseDAO
from app.donation.models import Donation
from app.database import async_session_maker
from sqlalchemy import select, update
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.common.enums import DonationStatus


class DonationDAO(BaseDAO):
    model = Donation
    
    @classmethod
    async def create_donation(cls, **donation_data) -> Donation:
        async with async_session_maker() as session:
            donation = cls.model(**donation_data)
            session.add(donation)
            await session.commit()
            await session.refresh(donation)
            return donation
    
    @classmethod
    async def get_donor_donations(cls, donor_id: int) -> List[Donation]:
        async with async_session_maker() as session:
            result = await session.execute(
                select(cls.model)
                .filter_by(donor_id=donor_id)
                .order_by(cls.model.donation_date.desc())
            )
            return result.scalars().all()
    
    @classmethod
    async def get_hospital_donations(cls, hospital_id: int) -> List[Donation]:
        async with async_session_maker() as session:
            result = await session.execute(
                select(cls.model)
                .filter_by(hospital_id=hospital_id)
                .order_by(cls.model.donation_date.desc())
            )
            return result.scalars().all()
    
    @classmethod
    async def get_request_donations(cls, blood_request_id: int) -> List[Donation]:
        async with async_session_maker() as session:
            result = await session.execute(
                select(cls.model)
                .filter_by(blood_request_id=blood_request_id)
                .order_by(cls.model.donation_date.desc())
            )
            return result.scalars().all()
    
    @classmethod
    async def complete_donation(cls, donation_id: int) -> Optional[Donation]:
        async with async_session_maker() as session:
            donation = await session.get(cls.model, donation_id)
            
            if not donation:
                return None
                
            if donation.complete():
                await session.commit()
                await session.refresh(donation)
                return donation
            
            return donation
    
    @classmethod
    async def cancel_donation(cls, donation_id: int, reason: Optional[str] = None) -> Optional[Donation]:
        """Cancel a donation"""
        async with async_session_maker() as session:
            donation = await session.get(cls.model, donation_id)
            
            if not donation:
                return None
                
            if donation.cancel(reason):
                await session.commit()
                await session.refresh(donation)
                return donation
            
            return donation
    
    @classmethod
    async def update_status(cls, donation_id: int, status: DonationStatus, reason: Optional[str] = None) -> Optional[Donation]:
        async with async_session_maker() as session:
            donation = await session.get(cls.model, donation_id)
            
            if not donation:
                return None
                
            donation.status = status
            
            if reason:
                donation.notes = reason if not donation.notes else f"{donation.notes}\n{reason}"
                
            await session.commit()
            await session.refresh(donation)
            return donation
        
    @classmethod
    async def get_donor_donations_with_sorting(cls, donor_id: int) -> List[Donation]:
        async with async_session_maker() as session:
            result = await session.execute(
                select(cls.model)
                .filter_by(donor_id=donor_id)
                .order_by(cls.model.donation_date.desc())
            )
            return result.scalars().all()
    
    @classmethod
    async def complete_donation(cls, donation_id: int) -> Optional[Donation]:
        async with async_session_maker() as session:
            donation = await session.get(cls.model, donation_id)
            
            if not donation:
                return None
                
            if donation.status != "scheduled":
                return None
                
            donation.status = "completed"
            donation.updated_at = datetime.now()
            

            if hasattr(donation, "donor") and donation.donor:
                donation.donor.last_donation_date = donation.donation_date
                donation.donor.total_donations += 1
                
            await session.commit()
            await session.refresh(donation)
            return donation
    
    @classmethod
    async def cancel_donation(cls, donation_id: int, reason: Optional[str] = None) -> Optional[Donation]:
        async with async_session_maker() as session:
            donation = await session.get(cls.model, donation_id)
            
            if not donation:
                return None
                
            if donation.status != "scheduled":
                return None
                
            donation.status = "cancelled"
            
            if reason:
                donation.notes = reason if not donation.notes else f"{donation.notes}\n{reason}"
                
            await session.commit()
            await session.refresh(donation)
            return donation
    
    @classmethod
    async def update(cls, instance_id: int, **values):
        async with async_session_maker() as session:
            instance = await session.get(cls.model, instance_id)
            if not instance:
                return None
            
            for key, value in values.items():
                setattr(instance, key, value)
            
            await session.commit()
            await session.refresh(instance)
            
            return instance