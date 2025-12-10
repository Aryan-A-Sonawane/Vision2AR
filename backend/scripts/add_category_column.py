"""
Add category column to tutorials table for proper data separation.

This allows filtering tutorials by category (PC, Mac, Computer Hardware, etc.)
to prevent mixing different device types in search results.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def migrate():
    """Add category column to tutorials table."""
    
    # Database configuration
    DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair")
    
    print("=" * 70)
    print("ADDING category COLUMN TO tutorials TABLE")
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
        AND column_name = 'category'
        """
        existing = await conn.fetch(check_query)
        
        if existing:
            print("[INFO] Column 'category' already exists. No changes needed.")
        else:
            # Add column
            alter_query = """
            ALTER TABLE tutorials 
            ADD COLUMN category VARCHAR(50);
            """
            await conn.execute(alter_query)
            print("[OK] Added column: category (VARCHAR 50)")
            
            # Add index for faster filtering
            index_query = """
            CREATE INDEX idx_tutorials_category 
            ON tutorials(category);
            """
            await conn.execute(index_query)
            print("[OK] Added index: idx_tutorials_category")
            print("     This allows fast filtering by category (PC/Mac/etc.)")
        
        # Show current schema (key columns only)
        schema_query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'tutorials'
        AND column_name IN ('id', 'brand', 'model', 'category', 'issue_type', 'title', 'source', 'myfixit_guideid')
        ORDER BY ordinal_position;
        """
        columns = await conn.fetch(schema_query)
        
        print("\nKey columns in tutorials table:")
        print("-" * 70)
        for col in columns:
            print(f"  {col['column_name']:25} {col['data_type']}")
        print("-" * 70)
        
        await conn.close()
        print("\n[SUCCESS] Migration complete!")
        print("\nCategory will store: 'PC', 'Mac', 'Computer Hardware', 'Phone', etc.")
        print("This prevents mixing laptop tutorials with phone/tablet repairs.")
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate())
