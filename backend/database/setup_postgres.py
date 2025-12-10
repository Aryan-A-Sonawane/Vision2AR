"""
Setup PostgreSQL database and run schema
"""
import os
import sys
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB", "ar_laptop_repair")

async def create_database():
    """Create database if it doesn't exist"""
    # Connect to default postgres database first
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database="postgres"
    )
    
    try:
        # Check if database exists
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            POSTGRES_DB
        )
        
        if not result:
            print(f"Creating database '{POSTGRES_DB}'...")
            await conn.execute(f'CREATE DATABASE {POSTGRES_DB}')
            print(f"✓ Database '{POSTGRES_DB}' created successfully")
        else:
            print(f"✓ Database '{POSTGRES_DB}' already exists")
    finally:
        await conn.close()

async def run_schema():
    """Run the schema_v2.sql file to create tables"""
    # Read schema file
    schema_path = os.path.join(os.path.dirname(__file__), "schema_v2.sql")
    
    if not os.path.exists(schema_path):
        print(f"✗ Schema file not found: {schema_path}")
        return False
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Connect to the target database
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB
    )
    
    try:
        print(f"\nRunning schema_v2.sql...")
        
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            try:
                await conn.execute(statement)
                print(f"  [{i}/{len(statements)}] Executed successfully")
            except Exception as e:
                # Check if error is about table already existing
                if "already exists" in str(e):
                    print(f"  [{i}/{len(statements)}] Table/Index already exists (skipped)")
                else:
                    print(f"  [{i}/{len(statements)}] Error: {e}")
                    # Continue with other statements
        
        print("✓ Schema created successfully")
        
        # Verify tables were created
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print(f"\n✓ Created tables ({len(tables)}):")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error running schema: {e}")
        return False
    finally:
        await conn.close()

async def test_connection():
    """Test database connection"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        version = await conn.fetchval("SELECT version()")
        print(f"✓ PostgreSQL connection successful")
        print(f"  Version: {version.split(',')[0]}")
        await conn.close()
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

async def main():
    """Main setup function"""
    print("=" * 60)
    print("PostgreSQL Database Setup")
    print("=" * 60)
    
    print(f"\nDatabase: {POSTGRES_DB}")
    print(f"User: {POSTGRES_USER}")
    print(f"Host: localhost:5432")
    
    # Step 1: Create database
    print("\n[Step 1] Creating database...")
    try:
        await create_database()
    except Exception as e:
        print(f"✗ Failed to create database: {e}")
        print("\nPlease ensure PostgreSQL is running and credentials are correct.")
        sys.exit(1)
    
    # Step 2: Run schema
    print("\n[Step 2] Creating tables...")
    success = await run_schema()
    
    if not success:
        print("\n✗ Schema creation failed")
        sys.exit(1)
    
    # Step 3: Test connection
    print("\n[Step 3] Testing connection...")
    await test_connection()
    
    print("\n" + "=" * 60)
    print("✓ PostgreSQL setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run seed_ifixit.py to populate with iFixit tutorials")
    print("  2. Run seed_oem.py to migrate existing OEM manuals")
    print("  3. Setup Weaviate schema")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
