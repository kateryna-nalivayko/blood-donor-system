import csv
import asyncio
from pathlib import Path
from datetime import datetime, date
from sqlalchemy import text
from app.database import async_session_maker

# Directory with CSV files
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Define column types for each table
COLUMN_TYPES = {
    "users": {
        "id": int,
        # All other columns can be strings by default
    },
    "donors": {
        "user_id": int,
        "weight": float,
        "height": float, 
        "date_of_birth": date.fromisoformat,
        "last_donation_date": date.fromisoformat,
        "first_donation_date": date.fromisoformat,
        "ineligible_until": date.fromisoformat,  # Add this missing field
        "total_donations": int
    },
    "hospitals": {
        "id": int,
        # All other columns can be strings by default
    },
    "hospital_staff": {
        "id": int,
        "user_id": int,
        "hospital_id": int
    },
    "blood_requests": {
        "hospital_id": int,
        "staff_id": int,
        "amount_needed_ml": int,
        "urgency_level": int,
        "request_date": datetime.fromisoformat,
        "needed_by_date": datetime.fromisoformat,
    },
    "donations": {
        "donor_id": int,
        "hospital_id": int,
        "blood_request_id": int, 
        "blood_amount_ml": int,
        "donation_date": datetime.fromisoformat
    }
}

async def clear_tables():
    """Clear all data from tables in reverse order of foreign key dependencies"""
    print("Clearing all tables...")
    
    # Order matters due to foreign key constraints (reverse of load order)
    tables = ["donations", "blood_requests", "hospital_staff", "donors", "hospitals", "users"]
    
    async with async_session_maker() as session:
        for table in tables:
            try:
                await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
                print(f"Cleared {table}")
            except Exception as e:
                print(f"Error clearing {table}: {e}")
        
        await session.commit()


async def insert_with_transaction(session, table_name, rows):
    """Insert rows with proper transaction handling"""
    success_count = 0
    
    for idx, row in enumerate(rows):
        try:
            # Process each value based on expected type
            for key in row:
                # Handle empty values
                if row[key] == '':
                    row[key] = None
                    continue
                
                # Handle boolean values
                if isinstance(row[key], str):  # Only check strings
                    if row[key].lower() == 'true':
                        row[key] = True
                        continue
                    elif row[key].lower() == 'false':
                        row[key] = False
                        continue
                
                # Handle data type conversions
                if table_name in COLUMN_TYPES and key in COLUMN_TYPES[table_name]:
                    try:
                        if row[key] is not None:
                            row[key] = COLUMN_TYPES[table_name][key](row[key])
                    except Exception as e:
                        print(f"Warning: Could not convert {key}='{row[key]}' to expected type: {e}")
            
            # Create query based on table
            columns = list(row.keys())
            placeholders = ', '.join([f':{col}' for col in columns])
            column_str = ', '.join(columns)
            
            # Build the SQL query
            query = text(f"INSERT INTO {table_name} ({column_str}) VALUES ({placeholders})")
            
            # Use a savepoint for each row (nested transaction)
            async with session.begin_nested():
                await session.execute(query, row)
                success_count += 1
                
        except Exception as e:
            # The nested transaction is automatically rolled back
            print(f"Error inserting row {idx+1}: {e}")
            print(f"Row data: {row}")
            # Continue processing other rows
    
    # Return the count of successful insertions
    return success_count



async def load_csv_to_db(file_path: str, table_name: str):
    """Load data from a CSV file into the specified table"""
    full_path = DATA_DIR / file_path
    
    if not full_path.exists():
        print(f"File not found: {full_path}")
        return 0
    
    async with async_session_maker() as session:
        try:
            with open(full_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
                if not rows:
                    print(f"No data found in {file_path}")
                    return 0
                
                # Use transaction-safe function to insert data
                count = await insert_with_transaction(session, table_name, rows)
                
                # Commit the transaction with all successful inserts
                await session.commit()
                print(f"Loaded {count} rows into {table_name}")
                return count
                
        except Exception as e:
            # Roll back on any unexpected error
            await session.rollback()
            print(f"Fatal error loading {table_name}: {e}")
            return 0
        
async def load_all_csvs(clear_first=False):
    if clear_first:
        await clear_tables()
        
    """Load all CSV files in the correct order to maintain relationships"""
    print("Loading CSV data into database...")
    
    # Load tables in order to maintain foreign key relationships
    await load_csv_to_db("users.csv", "users")
    await load_csv_to_db("hospitals.csv", "hospitals")
    await load_csv_to_db("donors.csv", "donors")
    await load_csv_to_db("hospital_staff.csv", "hospital_staff")
    await load_csv_to_db("blood_requests.csv", "blood_requests")
    
    # Before loading donations, check which donor_ids exist in the database
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT id FROM donors"))
        valid_donor_ids = [row[0] for row in result]
        
        # Load donations but filter out those with invalid donor_ids
        donations_path = DATA_DIR / "donations.csv"
        with open(donations_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            valid_rows = []
            
            for row in reader:
                try:
                    donor_id = int(row['donor_id'])
                    if donor_id in valid_donor_ids:
                        valid_rows.append(row)
                    else:
                        print(f"Skipping donation with invalid donor_id: {donor_id}")
                except (ValueError, KeyError):
                    print(f"Skipping row with invalid donor_id: {row.get('donor_id', 'N/A')}")
        
        if valid_rows:
            count = await insert_with_transaction(session, "donations", valid_rows)
            await session.commit()
            print(f"Loaded {count} valid rows into donations")
        else:
            print("No valid donation records found")
    
    print("CSV data loading complete!")

if __name__ == "__main__":
    import sys
    clear_first = "--clear" in sys.argv
    asyncio.run(load_all_csvs(clear_first))