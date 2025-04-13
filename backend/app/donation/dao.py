from app.dao.base import BaseDAO
from app.donation.models import Donation
from app.database import async_session_maker
from sqlalchemy import select, text, update
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.common.enums import BloodType, DonationStatus


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
        

    @classmethod
    async def find_donation_statistics_by_region(
        cls,
        min_donations: int = 10,
        min_total_ml: int = 5000,
        blood_type: Optional[str] = None,
        months: int = 3,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find hospital donation statistics grouped by region and blood type.
        
        Args:
            min_donations: Minimum number of donations received
            min_total_ml: Minimum total blood volume collected in ml
            blood_type: Optional blood type filter
            months: Look back period in months
            limit: Maximum number of results
        """
        async with async_session_maker() as session:
            params = {
                "min_donations": min_donations,
                "min_total_ml": min_total_ml,
                "months": months,
                "limit": limit
            }
            
            blood_type_clause = ""
            if blood_type:
                blood_type_enum = None
                for bt in BloodType:
                    if bt.value == blood_type:
                        blood_type_enum = bt.name
                        break
                        
                if blood_type_enum:
                    blood_type_clause = "AND d.blood_type = :blood_type"
                    params["blood_type"] = blood_type_enum
            
            query = text(f"""
            WITH hospital_stats AS (
                SELECT
                    h.id AS hospital_id,
                    h.name AS hospital_name,
                    h.city,
                    h.region,
                    d.blood_type,
                    COUNT(don.id) AS donation_count,
                    SUM(don.blood_amount_ml) AS total_collected_ml,
                    COUNT(DISTINCT d.id) AS unique_donors,
                    AVG(don.blood_amount_ml) AS avg_donation_ml
                FROM
                    hospitals h
                JOIN
                    donations don ON h.id = don.hospital_id
                JOIN
                    donors d ON don.donor_id = d.id
                WHERE
                    don.donation_date > NOW() - INTERVAL ':months months'
                    AND don.status = 'COMPLETED'
                    {blood_type_clause}
                GROUP BY
                    h.id, h.name, h.city, h.region, d.blood_type
                HAVING
                    COUNT(don.id) >= :min_donations
                    AND SUM(don.blood_amount_ml) >= :min_total_ml
            )
            SELECT
                hs.region,
                hs.blood_type,
                SUM(hs.donation_count) AS region_donation_count,
                SUM(hs.total_collected_ml) AS region_collected_ml,
                COUNT(DISTINCT hs.hospital_id) AS hospital_count,
                ROUND(AVG(hs.avg_donation_ml), 2) AS avg_donation_ml,
                SUM(hs.unique_donors) AS total_donors,
                STRING_AGG(hs.hospital_name, ', ') AS hospitals
            FROM
                hospital_stats hs
            GROUP BY
                hs.region, hs.blood_type
            ORDER BY
                region_collected_ml DESC,
                region
            LIMIT :limit
            """)
            
            result = await session.execute(query, params)
            
            statistics = []
            for row in result.mappings():
                stat_dict = dict(row)
                for bt in BloodType:
                    if bt.name == stat_dict['blood_type']:
                        stat_dict['blood_type'] = bt.value
                        break
                statistics.append(stat_dict)
                    
            return statistics
        

    @classmethod
    async def analyze_donation_demographics(
        cls,
        min_age: int = 18,
        max_age: int = 65,
        min_donations: int = 3,
        months: int = 12,
        group_by: str = "age_group",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Analyze donation frequency by demographics.
        
        Args:
            min_age: Minimum donor age
            max_age: Maximum donor age
            min_donations: Minimum number of donations per person
            months: Look back period in months
            group_by: Demographic grouping (age_group, gender, blood_type, region)
            limit: Maximum number of results
        """
        
        # Validate group_by parameter
        valid_groups = ["age_group", "gender", "blood_type", "region"]
        if group_by not in valid_groups:
            group_by = "age_group"
        
        async with async_session_maker() as session:
            case_statement = ""
            group_field = ""
            
            if group_by == "age_group":
                case_statement = """
                CASE 
                    WHEN DATE_PART('year', AGE(CURRENT_DATE, d.date_of_birth)) < 20 THEN '18-19'
                    WHEN DATE_PART('year', AGE(CURRENT_DATE, d.date_of_birth)) BETWEEN 20 AND 29 THEN '20-29'
                    WHEN DATE_PART('year', AGE(CURRENT_DATE, d.date_of_birth)) BETWEEN 30 AND 39 THEN '30-39'
                    WHEN DATE_PART('year', AGE(CURRENT_DATE, d.date_of_birth)) BETWEEN 40 AND 49 THEN '40-49'
                    WHEN DATE_PART('year', AGE(CURRENT_DATE, d.date_of_birth)) BETWEEN 50 AND 59 THEN '50-59'
                    ELSE '60+'
                END AS demographic_group"""
                group_field = "demographic_group"
            elif group_by == "gender":
                case_statement = "d.gender AS demographic_group"
                group_field = "demographic_group"
            elif group_by == "blood_type":
                case_statement = "d.blood_type AS demographic_group"
                group_field = "demographic_group"
            elif group_by == "region":
                case_statement = "h.region AS demographic_group"
                group_field = "demographic_group"
            
            query = text(f"""
            WITH donor_donation_counts AS (
                SELECT 
                    d.id AS donor_id,
                    {case_statement},
                    COUNT(don.id) AS donation_count,
                    SUM(don.blood_amount_ml) AS total_donated_ml,
                    MAX(don.donation_date) AS last_donation_date,
                    MIN(don.donation_date) AS first_donation_date
                FROM 
                    donors d
                JOIN 
                    donations don ON d.id = don.donor_id
                JOIN
                    hospitals h ON don.hospital_id = h.id
                WHERE 
                    don.donation_date > NOW() - INTERVAL ':months months'
                    AND don.status = 'COMPLETED'
                    AND DATE_PART('year', AGE(CURRENT_DATE, d.date_of_birth)) BETWEEN :min_age AND :max_age
                GROUP BY 
                    d.id, {group_field}
                HAVING 
                    COUNT(don.id) >= :min_donations
            )
            SELECT 
                demographic_group,
                COUNT(donor_id) AS donor_count,
                SUM(donation_count) AS total_donations,
                ROUND(AVG(donation_count), 2) AS avg_donations_per_donor,
                ROUND(SUM(total_donated_ml) / SUM(donation_count), 2) AS avg_donation_ml,
                MAX(donation_count) AS max_donations_by_donor,
                SUM(total_donated_ml) AS total_donated_ml,
                ROUND(AVG(DATE_PART('day', last_donation_date - first_donation_date) / donation_count), 2) AS avg_days_between_donations
            FROM 
                donor_donation_counts
            GROUP BY 
                demographic_group
            ORDER BY 
                total_donations DESC
            LIMIT :limit
            """)
            
            result = await session.execute(
                query, 
                {
                    "min_age": min_age,
                    "max_age": max_age,
                    "min_donations": min_donations,
                    "months": months,
                    "limit": limit
                }
            )
            
            demographics = []
            for row in result.mappings():
                demo_dict = dict(row)
                if group_by == "blood_type":
                    for bt in BloodType:
                        if bt.name == demo_dict['demographic_group']:
                            demo_dict['demographic_group'] = bt.value
                            break
                demographics.append(demo_dict)
                    
            return demographics