"""
Add unique constraint on myfixit_guideid column.

This allows ON CONFLICT (myfixit_guideid) DO UPDATE to work properly
to prevent duplicate ingestion of the same MyFixit guide.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def migrate():
    """Add unique constraint on myfixit_guideid."""
    
    # Database configuration
    DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair")
    
    print("=" * 70)
    print("ADDING UNIQUE CONSTRAINT ON myfixit_guideid")
    print("=" * 70)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DB_URL)
        print("[OK] Connected to database")
        
        # Check if constraint already exists
        check_query = """
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'tutorials'
        AND constraint_type = 'UNIQUE'
        AND constraint_name = 'tutorials_myfixit_guideid_unique'
        """
        existing = await conn.fetch(check_query)
        
        if existing:
            print("[INFO] Unique constraint already exists. No changes needed.")
        else:
            # Add unique constraint
            alter_query = """
            ALTER TABLE tutorials 
            ADD CONSTRAINT tutorials_myfixit_guideid_unique 
            UNIQUE (myfixit_guideid);
            """
            await conn.execute(alter_query)
            print("[OK] Added unique constraint: tutorials_myfixit_guideid_unique")
            print("     This allows safe re-ingestion (prevents duplicates)")
        
        # Show all constraints on tutorials table
        constraints_query = """
        SELECT constraint_name, constraint_type
        FROM information_schema.table_constraints
        WHERE table_name = 'tutorials'
        ORDER BY constraint_type, constraint_name;
        """
        constraints = await conn.fetch(constraints_query)
        
        print("\nConstraints on tutorials table:")
        print("-" * 70)
        for c in constraints:
            print(f"  {c['constraint_name']:40} {c['constraint_type']}")
        print("-" * 70)
        
        await conn.close()
        print("\n[SUCCESS] Migration complete!")
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate())
