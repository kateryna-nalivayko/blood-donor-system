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
            d.blood_type = 'B_POSITIVE'  
            AND don.status = 'COMPLETED'
        GROUP BY 
            u.id, u.first_name, u.last_name, u.email, u.phone_number, 
            d.id, d.blood_type
        HAVING 
            COUNT(don.id) >= 2  
        ORDER BY 
            donation_count DESC, last_donation_date DESC
        LIMIT 1000  