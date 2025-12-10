import asyncio
import asyncpg

async def check_api():
    conn = await asyncpg.connect('postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair')
    
    print("\n=== CHECKING API RESPONSE FORMAT ===")
    
    # Check what browse_tutorials returns
    results = await conn.fetch('''
        SELECT 
            id,
            brand,
            model,
            issue_type,
            title,
            difficulty,
            source,
            keywords
        FROM tutorials
        WHERE brand = 'hp' OR brand = 'lenovo'
        LIMIT 5
    ''')
    
    print("\nSample tutorial data from database:")
    for r in results:
        print(f"ID: {r['id']}, Brand: {r['brand']}, Title: {r['title'][:60]}")
    
    print("\n=== CHECKING SOURCE DISTRIBUTION ===")
    sources = await conn.fetch('''
        SELECT source, COUNT(*) as count
        FROM tutorials
        GROUP BY source
        ORDER BY count DESC
    ''')
    
    print("\nTutorials by source:")
    for s in sources:
        print(f"{s['source']}: {s['count']} tutorials")
    
    print("\n=== CHECKING IMAGE AVAILABILITY BY SOURCE ===")
    img_by_source = await conn.fetch('''
        SELECT t.source, 
               COUNT(DISTINCT t.id) as tutorial_count,
               COUNT(ts.image_url) as images_count
        FROM tutorials t
        LEFT JOIN tutorial_steps ts ON t.id = ts.tutorial_id
        GROUP BY t.source
        ORDER BY tutorial_count DESC
    ''')
    
    print("\nImage availability:")
    for i in img_by_source:
        print(f"{i['source']}: {i['tutorial_count']} tutorials, {i['images_count']} images")
    
    await conn.close()

asyncio.run(check_api())
