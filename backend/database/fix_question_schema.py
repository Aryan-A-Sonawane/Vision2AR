"""
Fix question_interactions table schema to match new code
"""
import asyncio
import asyncpg

async def fix_schema():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        database='ar_laptop_repair',
        user='postgres',
        password='9850044547'
    )
    
    print("\n🔧 Fixing question_interactions schema...")
    
    # Check current columns
    cols = await conn.fetch("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'question_interactions'
        ORDER BY ordinal_position
    """)
    
    print(f"\nCurrent columns: {[c['column_name'] for c in cols]}")
    
    # Drop old incompatible columns if they exist
    try:
        await conn.execute("ALTER TABLE question_interactions DROP COLUMN IF EXISTS belief_before_json CASCADE")
        print("✓ Dropped belief_before_json")
    except Exception as e:
        print(f"  (belief_before_json: {e})")
    
    try:
        await conn.execute("ALTER TABLE question_interactions DROP COLUMN IF EXISTS belief_after_json CASCADE")
        print("✓ Dropped belief_after_json")
    except Exception as e:
        print(f"  (belief_after_json: {e})")
    
    try:
        await conn.execute("ALTER TABLE question_interactions DROP COLUMN IF EXISTS user_answer CASCADE")
        print("✓ Dropped user_answer")
    except Exception as e:
        print(f"  (user_answer: {e})")
    
    # Check final schema
    cols_after = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'question_interactions'
        ORDER BY ordinal_position
    """)
    
    print(f"\n✅ Final schema:")
    for col in cols_after:
        print(f"  {col['column_name']:30} {col['data_type']}")
    
    await conn.close()
    print("\n🎉 Schema fix complete!\n")

if __name__ == "__main__":
    asyncio.run(fix_schema())
