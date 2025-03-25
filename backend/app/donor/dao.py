from app.dao.base import BaseDAO
from app.donor.models import Donor
from app.database import async_session_maker
from sqlalchemy import select
from typing import Optional
from datetime import date


class DonorDAO(BaseDAO):
    model = Donor

    @classmethod
    async def ensure_donor_profile(cls, user_id: int, 
                                  blood_type: str,
                                  gender: str,
                                  date_of_birth: date,
                                  weight: float,
                                  height: float,
                                  **additional_data) -> Donor:
        """
        Ensure a user has a donor profile, creating one if it doesn't exist.
        
        Args:
            user_id: ID of the user
            blood_type: Blood type of the donor
            gender: Gender of the donor
            date_of_birth: Date of birth
            weight: Weight in kg
            height: Height in cm
            additional_data: Any additional fields to set
            
        Returns:
            The existing or newly created Donor profile
        """
        async with async_session_maker() as session:
            # Check if profile already exists
            query = select(cls.model).filter_by(user_id=user_id)
            result = await session.execute(query)
            donor = result.scalar_one_or_none()
            
            if donor:
                return donor
            
            donor_data = {
                "user_id": user_id,
                "blood_type": blood_type,
                "gender": gender,
                "date_of_birth": date_of_birth,
                "weight": weight,
                "height": height,
                **additional_data
            }
            
            donor = cls.model(**donor_data)
            session.add(donor)
            await session.commit()
            await session.refresh(donor)
            
            return donor
        

    @classmethod
    async def update(cls, donor_id: int, **values) -> Optional[Donor]:
        """
        Update a donor profile with the given values.
        
        Args:
            donor_id: ID of the donor profile to update
            **values: Key-value pairs of fields to update
            
        Returns:
            Updated Donor instance or None if not found
        """
        async with async_session_maker() as session:
            donor = await session.execute(select(cls.model).filter_by(id=donor_id))
            donor = donor.scalar_one_or_none()
            
            if not donor:
                return None
            
            for key, value in values.items():
                if hasattr(donor, key):
                    setattr(donor, key, value)
            
            await session.commit()
            await session.refresh(donor)
            
            return donor