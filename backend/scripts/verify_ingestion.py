"""
Verify MyFixit ingestion results - check counts per category
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def verify_ingestion():
    """Query database to verify ingestion results"""
    
    DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair")
    
    print("=" * 70)
    print("VERIFYING MYFIXIT INGESTION RESULTS")
    print("=" * 70)
    
    conn = await asyncpg.connect(DB_URL)
    
    # Count tutorials by category
    print("\n[1] Tutorials by Category:")
    print("-" * 70)
    category_counts = await conn.fetch("""
        SELECT category, COUNT(*) as count
        FROM tutorials
        WHERE source = 'myfixit'
        GROUP BY category
        ORDER BY count DESC
    """)
    
    total_tutorials = 0
    for row in category_counts:
        cat = row['category'] if row['category'] else 'NULL'
        count = row['count']
        total_tutorials += count
        print(f"  {cat:30} {count:>6} tutorials")
    
    print(f"  {'TOTAL':30} {total_tutorials:>6} tutorials")
    
    # Count steps
    print("\n[2] Tutorial Steps:")
    print("-" * 70)
    step_stats = await conn.fetchrow("""
        SELECT 
            COUNT(*) as total_steps,
            COUNT(*) / NULLIF(COUNT(DISTINCT tutorial_id), 0) as avg_steps_per_tutorial
        FROM tutorial_steps ts
        JOIN tutorials t ON ts.tutorial_id = t.id
        WHERE t.source = 'myfixit'
    """)
    
    print(f"  Total steps: {step_stats['total_steps']:,}")
    print(f"  Average steps per tutorial: {float(step_stats['avg_steps_per_tutorial']):.1f}")
    
    # Count steps by category
    print("\n[3] Steps by Category:")
    print("-" * 70)
    steps_by_cat = await conn.fetch("""
        SELECT 
            t.category,
            COUNT(ts.id) as step_count,
            COUNT(ts.id) / NULLIF(COUNT(DISTINCT t.id), 0) as avg_steps
        FROM tutorial_steps ts
        JOIN tutorials t ON ts.tutorial_id = t.id
        WHERE t.source = 'myfixit'
        GROUP BY t.category
        ORDER BY step_count DESC
    """)
    
    for row in steps_by_cat:
        cat = row['category'] if row['category'] else 'NULL'
        steps = row['step_count']
        avg = float(row['avg_steps'])
        print(f"  {cat:30} {steps:>7} steps (avg {avg:.1f} per tutorial)")
    
    # Count tools
    print("\n[4] Tutorial Tools:")
    print("-" * 70)
    tool_stats = await conn.fetchrow("""
        SELECT 
            COUNT(*) as total_tool_entries,
            COUNT(DISTINCT tool_name) as unique_tools,
            COUNT(*) / NULLIF(COUNT(DISTINCT tutorial_id), 0) as avg_tools_per_tutorial
        FROM tutorial_tools tt
        JOIN tutorials t ON tt.tutorial_id = t.id
        WHERE t.source = 'myfixit'
    """)
    
    print(f"  Total tool entries: {tool_stats['total_tool_entries']:,}")
    print(f"  Unique tools: {tool_stats['unique_tools']:,}")
    print(f"  Average tools per tutorial: {float(tool_stats['avg_tools_per_tutorial']):.1f}")
    
    # Sample tutorials per category
    print("\n[5] Sample Tutorials by Category:")
    print("-" * 70)
    
    for category in ['PC', 'Mac', 'Computer Hardware']:
        samples = await conn.fetch("""
            SELECT id, brand, model, title, myfixit_guideid
            FROM tutorials
            WHERE source = 'myfixit' AND category = $1
            ORDER BY id
            LIMIT 3
        """, category)
        
        print(f"\n  {category}:")
        for sample in samples:
            print(f"    [{sample['id']}] {sample['title'][:60]}")
            print(f"         Brand: {sample['brand']} | Model: {sample['model']} | Guideid: {sample['myfixit_guideid']}")
    
    # Check for tutorials with images
    print("\n[6] Image Coverage:")
    print("-" * 70)
    image_stats = await conn.fetch("""
        SELECT 
            t.category,
            COUNT(DISTINCT t.id) as total_tutorials,
            COUNT(DISTINCT CASE WHEN ts.image_url IS NOT NULL THEN t.id END) as tutorials_with_images,
            COUNT(ts.image_url) as total_images
        FROM tutorials t
        LEFT JOIN tutorial_steps ts ON t.id = ts.tutorial_id
        WHERE t.source = 'myfixit'
        GROUP BY t.category
        ORDER BY total_tutorials DESC
    """)
    
    for row in image_stats:
        cat = row['category'] if row['category'] else 'NULL'
        total = row['total_tutorials']
        with_images = row['tutorials_with_images']
        images = row['total_images']
        pct = (with_images / total * 100) if total > 0 else 0
        print(f"  {cat:30} {with_images}/{total} tutorials ({pct:.1f}%) | {images:,} images")
    
    await conn.close()
    
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(verify_ingestion())
