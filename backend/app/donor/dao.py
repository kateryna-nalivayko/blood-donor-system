from app.dao.base import BaseDAO
from app.donor.models import Donor
from app.database import async_session_maker
from sqlalchemy import select, text
from typing import Optional, List, Dict, Any
from app.common.enums import BloodType
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
        

    @classmethod
    async def find_donors_by_blood_type_min_donations(
        cls,
        blood_type: str,
        min_donations: int = 1,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find donors with specific blood type who have made at least
        a minimum number of donations.
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
            SELECT 
                u.id AS user_id,
                u.first_name, 
                u.last_name, 
                u.email,
                u.phone_number,
                d.id AS donor_id,
                d.blood_type,
                COUNT(don.id) AS donation_count,
                SUM(don.blood_amount_ml) AS total_donated_ml,
                MAX(don.donation_date) AS last_donation_date
            FROM 
                users u
            JOIN 
                donors d ON u.id = d.user_id
            JOIN 
                donations don ON d.id = don.donor_id
            WHERE 
                d.blood_type = :blood_type
                AND don.status = 'COMPLETED'
            GROUP BY 
                u.id, u.first_name, u.last_name, u.email, u.phone_number, 
                d.id, d.blood_type
            HAVING 
                COUNT(don.id) >= :min_donations
            ORDER BY 
                donation_count DESC, last_donation_date DESC
            LIMIT :limit
            """)
            
            result = await session.execute(
                query, 
                {"blood_type": blood_type_enum, "min_donations": min_donations, "limit": limit}
            )
            

            donors = []
            for row in result.mappings():  
                donor_dict = dict(row)
                for bt in BloodType:
                    if bt.name == donor_dict['blood_type']:
                        donor_dict['blood_type'] = bt.value
                        break
                donors.append(donor_dict)
                
            return donors