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
        

    @classmethod
    async def find_eligible_donors_by_blood_type(
        cls,
        blood_type: str,
        days: int = 56,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find eligible donors with specific blood type who haven't donated in X days.
        
        Args:
            blood_type: Blood type to search for
            days: Minimum number of days since last donation
            limit: Maximum number of results to return
            
        Returns:
            List of eligible donors with their information
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
                d.id AS donor_id,
                u.first_name, 
                u.last_name, 
                u.email,
                u.phone_number,
                d.blood_type,
                d.last_donation_date,
                CASE 
                    WHEN d.last_donation_date IS NOT NULL THEN 
                        (CURRENT_DATE - d.last_donation_date)
                    ELSE NULL
                END AS days_since_donation,
                d.is_eligible,
                DATE_PART('year', AGE(CURRENT_DATE, d.date_of_birth)) AS age
            FROM 
                users u
            JOIN 
                donors d ON u.id = d.user_id
            WHERE 
                d.blood_type = :blood_type
                AND d.is_eligible = TRUE
                AND (
                    d.last_donation_date IS NULL 
                    OR (CURRENT_DATE - d.last_donation_date) >= :days
                )
                AND DATE_PART('year', AGE(CURRENT_DATE, d.date_of_birth)) BETWEEN 18 AND 65
            ORDER BY 
                d.last_donation_date ASC NULLS FIRST,
                u.last_name, 
                u.first_name
            LIMIT :limit
            """)
            
            result = await session.execute(
                query, 
                {"blood_type": blood_type_enum, "days": days, "limit": limit}
            )
            
            donors = []
            for row in result.mappings():  
                donor_dict = dict(row)
                for bt in BloodType:
                    if bt.name == donor_dict['blood_type']:
                        donor_dict['blood_type'] = bt.value
                        break
                
                donor_dict['can_donate'] = (
                    donor_dict['is_eligible'] and 
                    (donor_dict['age'] >= 18 and donor_dict['age'] <= 65) and
                    (donor_dict['days_since_donation'] is None or donor_dict['days_since_donation'] >= days)
                )
                
                donors.append(donor_dict)
                    
            return donors
        

    @classmethod
    async def find_multi_hospital_donors(
        cls,
        min_hospitals: int = 2,
        min_donations: int = 3,
        months: int = 6,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find donors who donated in multiple hospitals with at least a minimum number of total donations.
        """
        async with async_session_maker() as session:
            query = text("""
            SELECT 
                d.id AS donor_id,
                u.first_name, 
                u.last_name, 
                u.email,
                u.phone_number,
                d.blood_type,
                COUNT(DISTINCT don.hospital_id) AS hospital_count,
                COUNT(don.id) AS donation_count,
                SUM(don.blood_amount_ml) AS total_donated_ml,
                STRING_AGG(DISTINCT h.name, ', ') AS hospital_names
            FROM 
                donors d
            JOIN 
                users u ON d.user_id = u.id
            JOIN 
                donations don ON d.id = don.donor_id
            JOIN 
                hospitals h ON don.hospital_id = h.id
            WHERE 
                don.donation_date > NOW() - (:months * interval '1 month')
                AND don.status = 'COMPLETED'
            GROUP BY 
                d.id, u.first_name, u.last_name, u.email, u.phone_number, d.blood_type
            HAVING 
                COUNT(DISTINCT don.hospital_id) >= :min_hospitals
                AND COUNT(don.id) >= :min_donations
            ORDER BY 
                hospital_count DESC, donation_count DESC
            LIMIT :limit
            """)
            
            result = await session.execute(
                query, 
                {"min_hospitals": min_hospitals, "min_donations": min_donations, 
                 "months": months, "limit": limit}
            )
            
            
            result = await session.execute(
                query, 
                {"min_hospitals": min_hospitals, "min_donations": min_donations, 
                "months": months, "limit": limit}
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
        

    @classmethod
    async def find_universal_donors_by_region(
        cls,
        region: str,
        min_donations: int = 1,
        time_period_months: int = 12,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find donors who have donated to all hospitals in a specific region.
        
        Args:
            region: Region name to search within
            min_donations: Minimum number of donations per hospital
            time_period_months: Look at donations from the past N months
            limit: Maximum number of results to return
            
        Returns:
            List of donors who have donated to all hospitals in the region
        """
        async with async_session_maker() as session:
            query = text("""
            WITH region_hospitals AS (
                -- Get all hospitals in the specified region
                SELECT 
                    id, 
                    name,
                    city
                FROM 
                    hospitals
                WHERE 
                    region = :region
            ),
            region_hospital_count AS (
                -- Count how many hospitals are in the region
                SELECT COUNT(*) AS total_hospitals
                FROM region_hospitals
            ),
            donor_hospital_donations AS (
                -- Calculate how many hospitals each donor has donated to in the region
                SELECT 
                    d.id AS donor_id,
                    d.user_id,
                    u.first_name,
                    u.last_name,
                    u.email,
                    u.phone_number,
                    d.blood_type,
                    COUNT(DISTINCT don.hospital_id) AS hospitals_donated_to,
                    COUNT(don.id) AS total_donations,
                    SUM(don.blood_amount_ml) AS total_blood_ml,
                    STRING_AGG(DISTINCT h.name, ', ' ORDER BY h.name) AS hospital_names,
                    STRING_AGG(DISTINCT h.city, ', ' ORDER BY h.city) AS hospital_cities,
                    MIN(don.donation_date) AS first_donation_date,
                    MAX(don.donation_date) AS last_donation_date
                FROM 
                    donors d
                JOIN 
                    users u ON d.user_id = u.id
                JOIN 
                    donations don ON d.id = don.donor_id
                JOIN 
                    hospitals h ON don.hospital_id = h.id
                WHERE 
                    h.region = :region
                    AND don.status = 'COMPLETED'
                    AND don.donation_date >= CURRENT_DATE - INTERVAL ':months months'
                GROUP BY 
                    d.id, d.user_id, u.first_name, u.last_name, u.email, u.phone_number, d.blood_type
                HAVING
                    -- Make sure each hospital has at least min_donations donations
                    COUNT(DISTINCT don.hospital_id) > 0 AND
                    COUNT(don.id) >= COUNT(DISTINCT don.hospital_id) * :min_donations
            ),
            universal_donors AS (
                -- Find donors who have donated to all hospitals in the region
                SELECT 
                    dhd.*,
                    rhc.total_hospitals,
                    CASE 
                        WHEN dhd.hospitals_donated_to = rhc.total_hospitals THEN true
                        ELSE false
                    END AS is_universal_donor,
                    -- Calculate percentage of region covered
                    (dhd.hospitals_donated_to * 100.0 / NULLIF(rhc.total_hospitals, 0)) AS region_coverage_percent
                FROM 
                    donor_hospital_donations dhd
                CROSS JOIN 
                    region_hospital_count rhc
            )
            -- Final selection
            SELECT 
                ud.*,
                -- Add extra stats about the region
                (
                    SELECT COUNT(DISTINCT br.id)
                    FROM blood_requests br
                    JOIN hospitals h ON br.hospital_id = h.id
                    WHERE h.region = :region
                    AND br.request_date >= CURRENT_DATE - INTERVAL ':months months'
                ) AS total_region_requests,
                (
                    SELECT COUNT(DISTINCT h.id)
                    FROM hospitals h
                    WHERE h.region = :region
                ) AS total_region_hospitals
            FROM 
                universal_donors ud
            ORDER BY 
                ud.region_coverage_percent DESC,
                ud.total_donations DESC,
                ud.total_blood_ml DESC
            LIMIT :limit
            """)
            
            result = await session.execute(
                query, 
                {
                    "region": region,
                    "min_donations": min_donations,
                    "months": time_period_months,
                    "limit": limit
                }
            )
            
            return [dict(row) for row in result.mappings()]
        
    @classmethod
    async def find_universal_donors_by_region(
        cls,
        region: str,
        min_donations: int = 1,
        time_period_months: int = 12,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find donors who have donated blood in all hospitals within a region.
        """
        async with async_session_maker() as session:
            query = text("""
            WITH region_hospitals AS (
                -- All hospitals in the region
                SELECT
                    h.id,
                    h.name,
                    h.city
                FROM
                    hospitals h
                WHERE
                    h.region = :region
            ),
            region_stats AS (
                -- Get region statistics
                SELECT
                    :region AS region,
                    COUNT(h.id) AS total_region_hospitals,
                    (SELECT COUNT(*) FROM blood_requests br
                     WHERE br.hospital_id IN (SELECT h2.id FROM hospitals h2 WHERE h2.region = :region)
                     AND br.created_at >= NOW() - (:months * interval '1 month')
                    ) AS total_region_requests
                FROM 
                    hospitals h
                WHERE
                    h.region = :region
            ),
            donor_donations AS (
                -- Count donations per donor per hospital in the region
                SELECT
                    d.id AS donor_id,
                    d.user_id,
                    u.first_name,
                    u.last_name,
                    u.email,
                    d.blood_type,
                    don.hospital_id,
                    COUNT(don.id) AS donations_count,
                    SUM(don.blood_amount_ml) AS total_blood_ml,
                    MIN(don.donation_date) AS first_donation_date,
                    MAX(don.donation_date) AS last_donation_date
                FROM
                    donors d
                JOIN
                    users u ON d.user_id = u.id
                JOIN
                    donations don ON d.id = don.donor_id
                JOIN
                    hospitals h ON don.hospital_id = h.id
                WHERE
                    h.region = :region
                    AND don.status = 'COMPLETED'
                    AND don.donation_date >= NOW() - (:months * interval '1 month')
                GROUP BY
                    d.id, d.user_id, u.first_name, u.last_name, u.email, d.blood_type, don.hospital_id
                HAVING
                    COUNT(don.id) >= :min_donations
            ),
            donor_hospital_coverage AS (
                -- Summarize which donors donated to which hospitals
                SELECT
                    dd.donor_id,
                    dd.user_id,
                    dd.first_name,
                    dd.last_name,
                    dd.email,
                    dd.blood_type,
                    COUNT(DISTINCT dd.hospital_id) AS hospitals_donated_to,
                    (SELECT COUNT(*) FROM region_hospitals) AS total_hospitals,
                    COUNT(DISTINCT dd.hospital_id) * 100.0 / 
                        NULLIF((SELECT COUNT(*) FROM region_hospitals), 0) AS region_coverage_percent,
                    STRING_AGG(h.name, ', ' ORDER BY h.name) AS hospital_names,
                    STRING_AGG(DISTINCT h.city, ', ' ORDER BY h.city) AS hospital_cities,
                    MIN(dd.first_donation_date) AS first_donation_date,
                    SUM(dd.donations_count) AS total_donations,
                    SUM(dd.total_blood_ml) AS total_blood_ml,
                    MAX(dd.last_donation_date) AS last_donation_date
                FROM
                    donor_donations dd
                JOIN
                    hospitals h ON dd.hospital_id = h.id
                GROUP BY
                    dd.donor_id, dd.user_id, dd.first_name, dd.last_name, dd.email, dd.blood_type
            )
            -- Final selection
            SELECT
                dhc.*,
                rs.total_region_hospitals,
                rs.total_region_requests,
                dhc.hospitals_donated_to = dhc.total_hospitals AS is_universal_donor
            FROM
                donor_hospital_coverage dhc
            CROSS JOIN
                region_stats rs
            ORDER BY
                dhc.region_coverage_percent DESC,
                dhc.total_donations DESC,
                dhc.total_blood_ml DESC
            LIMIT :limit
            """)
            
            result = await session.execute(
                query, 
                {
                    "region": region,
                    "min_donations": min_donations,
                    "months": time_period_months,
                    "limit": limit
                }
            )
            
            return [dict(row) for row in result.mappings()]
        
  
    @classmethod
    async def find_donors_matching_multiple_requests(
        cls,
        min_match_count: int = 2,
        max_distance_km: float = 50.0,
        region: Optional[str] = None,
        blood_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find donors who can potentially fulfill multiple pending blood requests.
        
        This helps identify donors who can make a significant impact by addressing
        multiple blood needs in their vicinity.
        """
        async with async_session_maker() as session:
            # Створюємо динамічні умови для параметрів, які можуть бути None
            blood_type_filter = "TRUE" if blood_type is None else f"d.blood_type = '{blood_type}'"
            region_filter = "TRUE" if region is None else f"h.region = '{region}'"
            
            query = text(f"""
            WITH eligible_donors AS (
                -- Визначаємо донорів, які наразі є придатними
                SELECT
                    d.id AS donor_id,
                    u.first_name AS donor_first_name,
                    u.last_name AS donor_last_name,
                    d.blood_type,
                    u.phone_number,
                    u.email,
                    COALESCE(d.last_donation_date, '1900-01-01'::date) AS last_donation,
                    CURRENT_DATE - COALESCE(d.last_donation_date, '1900-01-01'::date) AS days_since_donation,
                    EXTRACT(YEAR FROM AGE(CURRENT_DATE, d.date_of_birth)) AS age,
                    d.weight,
                    d.height
                FROM
                    donors d
                JOIN
                    users u ON d.user_id = u.id
                WHERE
                    d.is_eligible = TRUE
                    AND (d.ineligible_until IS NULL OR d.ineligible_until < CURRENT_DATE)
                    AND {blood_type_filter}
            ),
            open_requests AS (
                -- Знаходимо відкриті запити на кров
                SELECT
                    br.id AS request_id,
                    br.blood_type,
                    br.amount_needed_ml,
                    br.urgency_level,
                    br.request_date,
                    br.hospital_id,
                    h.name AS hospital_name,
                    h.city AS hospital_city,
                    h.region AS hospital_region
                FROM
                    blood_requests br
                JOIN
                    hospitals h ON br.hospital_id = h.id
                WHERE
                    br.status IN ('PENDING', 'APPROVED')
                    AND {region_filter}
            ),
            compatible_matches AS (
                -- Знаходимо сумісності між донорами та запитами
                SELECT
                    d.donor_id,
                    d.donor_first_name,
                    d.donor_last_name,
                    d.blood_type AS donor_blood_type,
                    d.phone_number,
                    d.email,
                    d.days_since_donation,
                    d.age,
                    r.request_id,
                    r.blood_type AS request_blood_type,
                    r.amount_needed_ml,
                    r.urgency_level,
                    r.hospital_name,
                    r.hospital_city,
                    r.hospital_region,
                    -- Визначаємо сумісність груп крові
                    CASE
                        -- Універсальні донори O-негативної крові можуть здавати кров для будь-якої групи
                        WHEN d.blood_type = 'O_NEGATIVE' THEN TRUE
                        -- O-позитивна може бути передана для O+, A+, B+, AB+
                        WHEN d.blood_type = 'O_POSITIVE' AND r.blood_type IN ('O_POSITIVE', 'A_POSITIVE', 'B_POSITIVE', 'AB_POSITIVE') THEN TRUE
                        -- A-негативна може бути передана для A-, A+, AB-, AB+
                        WHEN d.blood_type = 'A_NEGATIVE' AND r.blood_type IN ('A_NEGATIVE', 'A_POSITIVE', 'AB_NEGATIVE', 'AB_POSITIVE') THEN TRUE
                        -- A-позитивна може бути передана для A+, AB+
                        WHEN d.blood_type = 'A_POSITIVE' AND r.blood_type IN ('A_POSITIVE', 'AB_POSITIVE') THEN TRUE
                        -- B-негативна може бути передана для B-, B+, AB-, AB+
                        WHEN d.blood_type = 'B_NEGATIVE' AND r.blood_type IN ('B_NEGATIVE', 'B_POSITIVE', 'AB_NEGATIVE', 'AB_POSITIVE') THEN TRUE
                        -- B-позитивна може бути передана для B+, AB+
                        WHEN d.blood_type = 'B_POSITIVE' AND r.blood_type IN ('B_POSITIVE', 'AB_POSITIVE') THEN TRUE
                        -- AB-негативна може бути передана для AB-, AB+
                        WHEN d.blood_type = 'AB_NEGATIVE' AND r.blood_type IN ('AB_NEGATIVE', 'AB_POSITIVE') THEN TRUE
                        -- AB-позитивна може бути передана тільки для AB+
                        WHEN d.blood_type = 'AB_POSITIVE' AND r.blood_type = 'AB_POSITIVE' THEN TRUE
                        ELSE FALSE
                    END AS is_compatible,
                    -- Визначаємо пріоритет відповідності (чим нижче значення, тим вищий пріоритет)
                    CASE
                        WHEN d.blood_type = r.blood_type THEN 1  -- Ідеальна відповідність
                        WHEN d.blood_type = 'O_NEGATIVE' THEN 2  -- Універсальний донор
                        ELSE 3  -- Сумісні, але не ідеальні
                    END AS match_priority
                FROM
                    eligible_donors d
                CROSS JOIN
                    open_requests r
                WHERE
                    -- Умови сумісності
                    CASE
                        WHEN d.blood_type = 'O_NEGATIVE' THEN TRUE
                        WHEN d.blood_type = 'O_POSITIVE' AND r.blood_type IN ('O_POSITIVE', 'A_POSITIVE', 'B_POSITIVE', 'AB_POSITIVE') THEN TRUE
                        WHEN d.blood_type = 'A_NEGATIVE' AND r.blood_type IN ('A_NEGATIVE', 'A_POSITIVE', 'AB_NEGATIVE', 'AB_POSITIVE') THEN TRUE
                        WHEN d.blood_type = 'A_POSITIVE' AND r.blood_type IN ('A_POSITIVE', 'AB_POSITIVE') THEN TRUE
                        WHEN d.blood_type = 'B_NEGATIVE' AND r.blood_type IN ('B_NEGATIVE', 'B_POSITIVE', 'AB_NEGATIVE', 'AB_POSITIVE') THEN TRUE
                        WHEN d.blood_type = 'B_POSITIVE' AND r.blood_type IN ('B_POSITIVE', 'AB_POSITIVE') THEN TRUE
                        WHEN d.blood_type = 'AB_NEGATIVE' AND r.blood_type IN ('AB_NEGATIVE', 'AB_POSITIVE') THEN TRUE
                        WHEN d.blood_type = 'AB_POSITIVE' AND r.blood_type = 'AB_POSITIVE' THEN TRUE
                        ELSE FALSE
                    END
                    -- Додаткова умова, що донор не здавав кров щонайменше 56 днів
                    AND d.days_since_donation >= 56
                    -- Імітація обмеження відстані
                    AND (random() * 100 <= :max_distance_km) 
            ),
            donor_match_counts AS (
                -- Підрахунок кількості запитів, які може задовольнити кожен донор
                SELECT
                    donor_id,
                    donor_first_name,
                    donor_last_name,
                    donor_blood_type,
                    phone_number,
                    email,
                    days_since_donation,
                    age,
                    COUNT(DISTINCT request_id) AS match_count,
                    COUNT(DISTINCT hospital_name) AS unique_hospitals,
                    COUNT(DISTINCT CASE WHEN match_priority = 1 THEN request_id END) AS perfect_matches,
                    STRING_AGG(DISTINCT hospital_name, ', ' ORDER BY hospital_name) AS matched_hospitals,
                    STRING_AGG(DISTINCT request_blood_type::text, ', ' ORDER BY request_blood_type::text) AS matched_blood_types
                FROM
                    compatible_matches
                GROUP BY
                    donor_id, donor_first_name, donor_last_name, donor_blood_type, 
                    phone_number, email, days_since_donation, age
                HAVING
                    COUNT(DISTINCT request_id) >= :min_match_count
            )
            -- Вибір кінцевого результату
            SELECT
                donor_id,
                donor_first_name || ' ' || donor_last_name AS donor_name,
                donor_blood_type,
                phone_number,
                email,
                match_count,
                perfect_matches,
                unique_hospitals,
                ROUND(perfect_matches::numeric * 100.0 / match_count, 1) AS perfect_match_percent,
                matched_hospitals,
                matched_blood_types,
                days_since_donation,
                age
            FROM
                donor_match_counts
            ORDER BY
                match_count DESC,
                perfect_match_percent DESC,
                days_since_donation DESC
            LIMIT :limit
            """)
            
            result = await session.execute(
                query, 
                {
                    "min_match_count": min_match_count,
                    "max_distance_km": max_distance_km,
                    "limit": limit
                }
            )
            
            return [dict(row) for row in result.mappings()]