"""
Quick verification of learning system tables
"""
import asyncio
import asyncpg

async def check_learning_tables():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        database='ar_laptop_repair',
        user='postgres',
        password='9850044547'
    )
    
    print("\n" + "="*70)
    print("📊 LEARNING SYSTEM DATABASE VERIFICATION")
    print("="*70)
    
    # Check which tables exist
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
    
    print(f"\n✅ Found {len(tables)}/11 Learning Tables:")
    table_names = [row['table_name'] for row in tables]
    for name in table_names:
        print(f"  ✓ {name}")
    
    # Check row counts
    print(f"\n📈 Current Data (Row Counts):")
    for name in table_names:
        count = await conn.fetchval(f"SELECT COUNT(*) FROM {name}")
        print(f"  {name:30} {count:>8} rows")
    
    # Check if any sessions exist
    if 'diagnostic_sessions' in table_names:
        recent_sessions = await conn.fetch("""
            SELECT session_id, device_category, final_diagnosis, problem_resolved, created_at
            FROM diagnostic_sessions
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if recent_sessions:
            print(f"\n🔍 Recent Diagnostic Sessions:")
            for s in recent_sessions:
                status = "✓ Resolved" if s['problem_resolved'] else "⏳ In Progress"
                print(f"  {s['created_at']} | {s['device_category']:12} | {s['final_diagnosis'] or 'N/A':20} | {status}")
        else:
            print(f"\n⚠️  No diagnostic sessions yet - need to test the system!")
    
    # Check if any patterns discovered
    if 'pattern_candidates' in table_names:
        patterns = await conn.fetchval("SELECT COUNT(*) FROM pattern_candidates")
        if patterns > 0:
            print(f"\n🧠 Pattern Discovery: {patterns} candidate patterns found!")
        else:
            print(f"\n💤 Pattern Discovery: No patterns yet (need more sessions)")
    
    # Check image caching
    if 'image_caption_cache' in table_names:
        cached_images = await conn.fetchval("SELECT COUNT(*) FROM image_caption_cache")
        if cached_images > 0:
            print(f"\n📸 BLIP-2 Cache: {cached_images} images cached")
        else:
            print(f"\n📸 BLIP-2 Cache: Empty (no images analyzed yet)")
    
    await conn.close()
    print(f"\n" + "="*70)
    print("✅ Verification Complete")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(check_learning_tables())
