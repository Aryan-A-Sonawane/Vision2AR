"""
Add myfixit_guideid column to tutorials table.

This migration adds the myfixit_guideid column that tracks the original
iFixit guide ID for tutorials sourced from MyFixit dataset.
"""

import asyncio
import asyncpg
import os


async def migrate():
    """Add myfixit_guideid column to tutorials table."""
    
    # Database configuration - use same as ingest_myfixit.py
    DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair")
    
    print("=" * 70)
    print("ADDING myfixit_guideid COLUMN TO tutorials TABLE")
    print("=" * 70)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DB_URL)
        print("[OK] Connected to database")
        
        # Check if column already exists
        check_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'tutorials' 
        AND column_name = 'myfixit_guideid'
        """
        existing = await conn.fetch(check_query)
        
        if existing:
            print("[INFO] Column myfixit_guideid already exists. No changes needed.")
        else:
            # Add column
            alter_query = """
            ALTER TABLE tutorials 
            ADD COLUMN myfixit_guideid INTEGER;
            """
            await conn.execute(alter_query)
            print("[OK] Added column: myfixit_guideid (INTEGER)")
            
            # Add index for faster lookups
            index_query = """
            CREATE INDEX idx_tutorials_myfixit_guideid 
            ON tutorials(myfixit_guideid);
            """
            await conn.execute(index_query)
            print("[OK] Added index: idx_tutorials_myfixit_guideid")
        
        # Show current schema
        schema_query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'tutorials'
        ORDER BY ordinal_position;
        """
        columns = await conn.fetch(schema_query)
        
        print("\nCurrent tutorials table schema:")
        print("-" * 70)
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  {col['column_name']:25} {col['data_type']:15} {nullable}")
        print("-" * 70)
        
        await conn.close()
        print("\n[SUCCESS] Migration complete!")
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate())
