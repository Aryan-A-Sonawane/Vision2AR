import asyncio
import asyncpg

async def check_images():
    conn = await asyncpg.connect('postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair')
    
    print("\n=== TUTORIALS BY BRAND ===")
    brands = await conn.fetch('''
        SELECT brand, COUNT(*) as count 
        FROM tutorials 
        GROUP BY brand 
        ORDER BY count DESC 
        LIMIT 10
    ''')
    for b in brands:
        print(f"{b['brand']}: {b['count']}")
    
    print("\n=== SAMPLE TUTORIALS WITH IMAGE DATA ===")
    samples = await conn.fetch('''
        SELECT t.id, t.brand, t.model, t.title,
               COUNT(ts.id) as step_count, 
               COUNT(ts.image_url) as images,
               COUNT(CASE WHEN ts.image_url IS NOT NULL THEN 1 END) as non_null_images
        FROM tutorials t 
        LEFT JOIN tutorial_steps ts ON t.id = ts.tutorial_id
        WHERE t.brand IN ('lenovo', 'hp', 'sony')
        GROUP BY t.id, t.brand, t.model, t.title
        ORDER BY t.brand, t.id 
        LIMIT 20
    ''')
    for s in samples:
        print(f"ID {s['id']}: {s['brand']} {s['model']} - Steps: {s['step_count']}, Images: {s['non_null_images']}/{s['step_count']}")
        
    print("\n=== CHECKING SPECIFIC TUTORIAL IDS ===")
    specific = await conn.fetch('''
        SELECT ts.tutorial_id, ts.step_number, 
               ts.title,
               CASE WHEN ts.image_url IS NULL THEN 'NO IMAGE' ELSE 'HAS IMAGE' END as img_status
        FROM tutorial_steps ts
        WHERE ts.tutorial_id IN (74, 100, 200, 300)
        ORDER BY ts.tutorial_id, ts.step_number
        LIMIT 30
    ''')
    for s in specific:
        print(f"Tutorial {s['tutorial_id']} Step {s['step_number']}: {s['img_status']} - {s['title'][:50] if s['title'] else 'No title'}")
    
    print("\n=== TUTORIALS WITH IMAGES (myfixit source) ===")
    with_images = await conn.fetch('''
        SELECT t.id, t.brand, t.model, t.source, COUNT(ts.image_url) as image_count
        FROM tutorials t
        LEFT JOIN tutorial_steps ts ON t.id = ts.tutorial_id
        WHERE ts.image_url IS NOT NULL
        GROUP BY t.id
        ORDER BY t.id
        LIMIT 20
    ''')
    for t in with_images:
        print(f"ID {t['id']}: {t['brand']} {t['model']} ({t['source']}) - {t['image_count']} images")
    
    await conn.close()

asyncio.run(check_images())
