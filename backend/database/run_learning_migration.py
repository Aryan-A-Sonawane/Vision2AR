"""
Execute learning schema migration
Creates all 11 tables for self-learning diagnostic system
"""
import asyncio
import asyncpg
from pathlib import Path

async def run_migration():
    """Execute schema_learning.sql"""
    
    # Database connection
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        database="ar_laptop_repair",
        user="postgres",
        password="9850044547"
    )
    
    print("✅ Connected to PostgreSQL")
    
    # Read SQL file
    sql_path = Path(__file__).parent / "schema_learning.sql"
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    print(f"📄 Loaded {sql_path.name}")
    
    try:
        # Execute the entire script
        await conn.execute(sql_script)
        print("✅ Schema migration completed successfully")
        
        # Verify tables were created
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (
                'diagnostic_sessions',
                'diagnostic_logs',
                'belief_snapshots',
                'question_interactions',
                'tutorial_matches',
                'user_feedback',
                'learned_patterns',
                'learned_questions',
                'pattern_candidates',
                'question_analytics',
                'image_caption_cache'
            )
            ORDER BY table_name
        """)
        
        print(f"\n📊 Created {len(tables)} tables:")
        for row in tables:
            print(f"  ✓ {row['table_name']}")
        
        # Check indexes
        indexes = await conn.fetch("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename IN (
                'diagnostic_sessions',
                'diagnostic_logs',
                'belief_snapshots',
                'question_interactions',
                'tutorial_matches',
                'user_feedback',
                'learned_patterns',
                'learned_questions',
                'pattern_candidates',
                'question_analytics',
                'image_caption_cache'
            )
        """)
        
        print(f"\n🔍 Created {len(indexes)} indexes")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(run_migration())
