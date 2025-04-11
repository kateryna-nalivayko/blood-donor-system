import asyncio
import subprocess
from sqlalchemy import text
from app.database import async_session_maker

async def drop_enum_types():
    """Drop all PostgreSQL enum types to prevent 'type already exists' errors"""
    print("Dropping PostgreSQL enum types...")
    
    # These names match your app/common/enums.py declarations
    # PostgreSQL stores them in lowercase with "_type" suffix for SQLAlchemy enums
    enum_types = [
        "bloodtype",
        "staffrole", 
        "department",
        "hospitaltype",
        "requeststatus",
        "donationstatus",
        "gender"  # This might be defined elsewhere in your code
    ]
    
    async with async_session_maker() as session:
        for enum_type in enum_types:
            try:
                await session.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE;"))
                print(f"✓ Dropped enum type: {enum_type}")
            except Exception as e:
                print(f"✗ Error dropping {enum_type}: {e}")
        await session.commit()

async def reset_database():
    """Reset the entire database"""
    print("Starting database reset...")
    
    # Step 1: Drop all enum types first 
    await drop_enum_types()
    
    # Step 2: Use Alembic to reset schema
    print("\nResetting schema using Alembic...")
    subprocess.run(["alembic", "downgrade", "base"])
    subprocess.run(["alembic", "upgrade", "head"])
    
    # Step 3: Verify database is clean
    print("\nVerifying database is reset...")
    tables = ["users", "hospitals", "donors", "hospital_staff", "blood_requests", "donations"]
    async with async_session_maker() as session:
        for table in tables:
            try:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"✓ Table {table}: {count} records")
            except Exception as e:
                print(f"✗ Error checking {table}: {e}")
    
    print("\nDatabase reset complete!")

if __name__ == "__main__":
    asyncio.run(reset_database())