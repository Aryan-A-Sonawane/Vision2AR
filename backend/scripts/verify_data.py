"""
Quick verification script to check both PostgreSQL and Weaviate data
"""
import asyncio
import asyncpg
import weaviate
from dotenv import load_dotenv
import os

load_dotenv()

async def check_postgresql():
    """Check PostgreSQL data"""
    print("\n" + "="*70)
    print("📊 POSTGRESQL DATA VERIFICATION")
    print("="*70)
    
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        database="ar_laptop_repair",
        user="postgres",
        password="9850044547"
    )
    
    try:
        # Count tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print(f"\n✅ Total tables: {len(tables)}")
        print("\nAll tables:")
        for i, row in enumerate(tables, 1):
            print(f"  {i:2d}. {row['table_name']}")
        
        # Count data in key tables
        print("\n" + "-"*70)
        print("Data counts:")
        
        key_tables = [
            'tutorials',
            'tutorial_steps',
            'diagnostic_sessions',
            'learned_patterns',
            'pattern_candidates',
            'user_feedback'
        ]
        
        for table in key_tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            status = "✅" if count > 0 else "⚪"
            print(f"  {status} {table:25s}: {count:4d} rows")
        
        # Show sample tutorials
        print("\n" + "-"*70)
        print("Sample tutorials:")
        tutorials = await conn.fetch("""
            SELECT id, brand, model, issue_type, title, source
            FROM tutorials
            LIMIT 5
        """)
        
        for t in tutorials:
            print(f"\n  ID {t['id']}: {t['brand']} {t['model']}")
            print(f"    Issue: {t['issue_type']}")
            print(f"    Title: {t['title'][:60]}...")
            print(f"    Source: {t['source']}")
        
    finally:
        await conn.close()

def check_weaviate():
    """Check Weaviate data"""
    print("\n\n" + "="*70)
    print("🔍 WEAVIATE VECTOR DATA VERIFICATION")
    print("="*70)
    
    client = weaviate.Client(
        url=os.getenv("WEAVIATE_URL"),
        auth_client_secret=weaviate.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY"))
    )
    
    try:
        # Check schema
        schema = client.schema.get()
        print(f"\n✅ Schema classes: {len(schema['classes'])}")
        
        for cls in schema['classes']:
            print(f"\n  Class: {cls['class']}")
            print(f"    Properties: {len(cls['properties'])}")
            for prop in cls['properties']:
                print(f"      - {prop['name']} ({prop['dataType'][0]})")
        
        # Count objects
        result = client.query.aggregate("Tutorial").with_meta_count().do()
        count = result['data']['Aggregate']['Tutorial'][0]['meta']['count']
        
        print(f"\n✅ Total Tutorial objects: {count}")
        
        # Sample data
        print("\n" + "-"*70)
        print("Sample tutorials:")
        
        results = client.query.get(
            "Tutorial",
            ["brand", "model", "issue_type", "title", "difficulty"]
        ).with_limit(5).do()
        
        if 'data' in results and 'Get' in results['data']:
            tutorials = results['data']['Get']['Tutorial']
            for i, t in enumerate(tutorials, 1):
                print(f"\n  {i}. {t.get('brand', 'N/A')} {t.get('model', 'N/A')}")
                print(f"     Issue: {t.get('issue_type', 'N/A')}")
                print(f"     Title: {t.get('title', 'N/A')[:60]}...")
                print(f"     Difficulty: {t.get('difficulty', 'N/A')}")
        
        # Test vector search
        print("\n" + "-"*70)
        print("Test vector search (query: 'laptop won't turn on'):")
        
        search_results = client.query.get(
            "Tutorial",
            ["brand", "model", "title", "issue_type"]
        ).with_near_text({
            "concepts": ["laptop won't turn on"]
        }).with_limit(3).do()
        
        if 'data' in search_results and 'Get' in search_results['data']:
            matches = search_results['data']['Get']['Tutorial']
            for i, m in enumerate(matches, 1):
                print(f"\n  {i}. {m.get('brand', 'N/A')} - {m.get('issue_type', 'N/A')}")
                print(f"     {m.get('title', 'N/A')[:60]}...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

async def main():
    """Run all checks"""
    print("\n" + "🔍 "*35)
    print("DATA VERIFICATION REPORT")
    print("🔍 "*35)
    
    # PostgreSQL check
    await check_postgresql()
    
    # Weaviate check
    check_weaviate()
    
    print("\n\n" + "="*70)
    print("✅ VERIFICATION COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("  1. Open pgAdmin to browse tables visually")
    print("  2. Visit https://console.weaviate.cloud/ to explore vector data")
    print("  3. Ready to proceed with core implementation!")
    print()

if __name__ == "__main__":
    asyncio.run(main())
