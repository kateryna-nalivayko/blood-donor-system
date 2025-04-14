from typing import Dict, List, Any, Optional
from sqlalchemy import text
from app.database import async_session_maker

class TablesDAO:
    """Data Access Object for direct SQL queries to database tables."""

    @classmethod
    async def get_table_data(
        cls,
        table_name: str,
        page: int = 1,
        limit: int = 25,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch data from a specific table with pagination and optional search.
        
        Args:
            table_name: The name of the table to query
            page: Page number (1-indexed)
            limit: Number of records per page
            search: Optional search string for filtering
            
        Returns:
            Dictionary with items, total count, current page, and total pages
        """
        async with async_session_maker() as session:
            offset = (page - 1) * limit
            
            # Build the SQL query based on table name
            if search:
                search_param = f"%{search}%"
            else:
                search_param = None
                
            # Define query parameters and search conditions based on table name
            query_params = {"limit": limit, "offset": offset}
            count_params = {}
            
            # Configure search conditions for specific tables
            search_conditions = ""
            
            # Build table-specific queries
            if table_name == "users":
                if search:
                    search_conditions = """
                        WHERE first_name ILIKE :search 
                        OR last_name ILIKE :search
                        OR email ILIKE :search
                        OR phone_number ILIKE :search
                    """
                    query_params["search"] = search_param
                    count_params["search"] = search_param
                
                query = text(f"""
                    SELECT 
                        id, 
                        first_name, 
                        last_name, 
                        email, 
                        phone_number, 
                        is_donor, 
                        is_hospital_staff,
                        is_admin,
                        is_super_admin,
                        created_at,
                        updated_at
                    FROM users
                    {search_conditions}
                    ORDER BY id
                    LIMIT :limit OFFSET :offset
                """)
                
                count_query = text(f"""
                    SELECT COUNT(*) as total FROM users {search_conditions}
                """)
                
            elif table_name == "donors":
                if search:
                    search_conditions = """
                        WHERE blood_type ILIKE :search
                        OR id::text ILIKE :search
                        OR user_id::text ILIKE :search
                    """
                    query_params["search"] = search_param
                    count_params["search"] = search_param
                
                query = text(f"""
                    SELECT 
                        d.id, 
                        d.user_id, 
                        d.gender, 
                        d.date_of_birth,
                        d.blood_type,
                        d.weight,
                        d.height,
                        d.is_eligible,
                        d.total_donations,
                        d.last_donation_date,
                        d.first_donation_date,
                        u.first_name,
                        u.last_name
                    FROM donors d
                    JOIN users u ON d.user_id = u.id
                    {search_conditions}
                    ORDER BY d.id
                    LIMIT :limit OFFSET :offset
                """)
                
                count_query = text(f"""
                    SELECT COUNT(*) as total FROM donors d
                    JOIN users u ON d.user_id = u.id
                    {search_conditions}
                """)
                
            elif table_name == "hospitals":
                if search:
                    search_conditions = """
                        WHERE name ILIKE :search
                        OR city ILIKE :search
                        OR region ILIKE :search
                    """
                    query_params["search"] = search_param
                    count_params["search"] = search_param
                
                query = text(f"""
                    SELECT 
                        id, 
                        name,
                        hospital_type,
                        address,
                        city,
                        region,
                        country,
                        phone_number,
                        email,
                        website,
                        created_at
                    FROM hospitals
                    {search_conditions}
                    ORDER BY id
                    LIMIT :limit OFFSET :offset
                """)
                
                count_query = text(f"""
                    SELECT COUNT(*) as total FROM hospitals {search_conditions}
                """)
                
            elif table_name == "hospital_staff":
                if search:
                    search_conditions = """
                        WHERE hs.id::text ILIKE :search
                        OR h.name ILIKE :search
                        OR u.first_name ILIKE :search
                        OR u.last_name ILIKE :search
                        OR hs.role ILIKE :search
                        OR hs.department ILIKE :search
                    """
                    query_params["search"] = search_param
                    count_params["search"] = search_param
                
                query = text(f"""
                    SELECT 
                        hs.id, 
                        hs.user_id,
                        hs.hospital_id,
                        hs.role,
                        hs.department,
                        u.first_name,
                        u.last_name,
                        h.name as hospital_name,
                        h.city as hospital_city,
                        hs.created_at
                    FROM hospital_staff hs
                    JOIN users u ON hs.user_id = u.id
                    JOIN hospitals h ON hs.hospital_id = h.id
                    {search_conditions}
                    ORDER BY hs.id
                    LIMIT :limit OFFSET :offset
                """)
                
                count_query = text(f"""
                    SELECT COUNT(*) as total 
                    FROM hospital_staff hs
                    JOIN users u ON hs.user_id = u.id
                    JOIN hospitals h ON hs.hospital_id = h.id
                    {search_conditions}
                """)
                
            elif table_name == "blood_requests":
                if search:
                    search_conditions = """
                        WHERE br.id::text ILIKE :search
                        OR br.blood_type ILIKE :search
                        OR h.name ILIKE :search
                        OR br.status ILIKE :search
                    """
                    query_params["search"] = search_param
                    count_params["search"] = search_param
                
                query = text(f"""
                    SELECT 
                        br.id, 
                        br.hospital_id,
                        br.staff_id,
                        br.blood_type,
                        br.amount_needed_ml,
                        br.urgency_level,
                        br.status,
                        br.request_date,
                        br.needed_by_date,
                        h.name as hospital_name,
                        u.first_name,
                        u.last_name,
                        (
                            SELECT COALESCE(SUM(d.blood_amount_ml), 0)
                            FROM donations d
                            WHERE d.blood_request_id = br.id AND d.status = 'COMPLETED'
                        ) as collected_amount
                    FROM blood_requests br
                    JOIN hospital_staff hs ON br.staff_id = hs.id
                    JOIN users u ON hs.user_id = u.id
                    JOIN hospitals h ON br.hospital_id = h.id
                    {search_conditions}
                    ORDER BY br.id DESC
                    LIMIT :limit OFFSET :offset
                """)
                
                count_query = text(f"""
                    SELECT COUNT(*) as total 
                    FROM blood_requests br
                    JOIN hospital_staff hs ON br.staff_id = hs.id
                    JOIN users u ON hs.user_id = u.id
                    JOIN hospitals h ON br.hospital_id = h.id
                    {search_conditions}
                """)
                
            elif table_name == "donations":
                if search:
                    search_conditions = """
                        WHERE d.id::text ILIKE :search
                        OR d.blood_type ILIKE :search
                        OR d.status ILIKE :search
                        OR h.name ILIKE :search
                        OR u.first_name ILIKE :search
                        OR u.last_name ILIKE :search
                    """
                    query_params["search"] = search_param
                    count_params["search"] = search_param
                
                query = text(f"""
                    SELECT 
                        d.id, 
                        d.donor_id,
                        d.hospital_id,
                        d.blood_request_id,
                        d.blood_amount_ml,
                        d.blood_type,
                        d.donation_date,
                        d.status,
                        h.name as hospital_name,
                        u.first_name,
                        u.last_name,
                        br.id as request_id
                    FROM donations d
                    JOIN donors dn ON d.donor_id = dn.id
                    JOIN users u ON dn.user_id = u.id
                    JOIN hospitals h ON d.hospital_id = h.id
                    LEFT JOIN blood_requests br ON d.blood_request_id = br.id
                    {search_conditions}
                    ORDER BY d.donation_date DESC
                    LIMIT :limit OFFSET :offset
                """)
                
                count_query = text(f"""
                    SELECT COUNT(*) as total 
                    FROM donations d
                    JOIN donors dn ON d.donor_id = dn.id
                    JOIN users u ON dn.user_id = u.id
                    JOIN hospitals h ON d.hospital_id = h.id
                    LEFT JOIN blood_requests br ON d.blood_request_id = br.id
                    {search_conditions}
                """)
            else:
                # Handle unknown table name
                return {
                    "items": [],
                    "total": 0,
                    "page": page,
                    "pages": 0
                }
            
            # Execute the query
            result = await session.execute(query, query_params)
            items = [dict(row) for row in result.mappings()]
            
            # Get total count
            count_result = await session.execute(count_query, count_params)
            total = count_result.scalar()
            
            # Calculate total pages
            pages = (total + limit - 1) // limit
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "pages": pages
            }