import asyncio
import asyncpg

async def check_indices():
    conn = await asyncpg.connect('postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair')
    
    print("\n=== TUTORIAL INDICES BY CATEGORY ===\n")
    
    # Get category distribution with min/max IDs
    categories = await conn.fetch('''
        SELECT 
            category,
            COUNT(*) as count,
            MIN(id) as min_id,
            MAX(id) as max_id,
            source
        FROM tutorials
        WHERE source = 'myfixit'
        GROUP BY category, source
        ORDER BY min_id
    ''')
    
    print("Category breakdown (myfixit source with images):")
    print("-" * 80)
    for cat in categories:
        print(f"{cat['category']:20} | IDs {cat['min_id']:5} to {cat['max_id']:5} | {cat['count']:5} tutorials")
    
    print("\n" + "=" * 80)
    print("\nBrand/Model breakdown (top categories):")
    print("-" * 80)
    
    # Get more detailed breakdown by brand for main categories
    laptops = await conn.fetch('''
        SELECT brand, model, COUNT(*) as count, MIN(id) as min_id, MAX(id) as max_id
        FROM tutorials
        WHERE source = 'myfixit' 
        AND (category = 'PC' OR brand LIKE '%laptop%' OR model LIKE '%laptop%')
        GROUP BY brand, model
        ORDER BY min_id
        LIMIT 30
    ''')
    
    print("\nLAPTOP/PC Tutorials:")
    for item in laptops[:15]:
        print(f"  {item['brand']:15} {item['model']:30} | IDs {item['min_id']:5}-{item['max_id']:5} | {item['count']:3} guides")
    
    phones = await conn.fetch('''
        SELECT brand, model, COUNT(*) as count, MIN(id) as min_id, MAX(id) as max_id
        FROM tutorials
        WHERE source = 'myfixit' 
        AND category = 'Phone'
        GROUP BY brand, model
        ORDER BY min_id
        LIMIT 20
    ''')
    
    print("\nPHONE Tutorials:")
    for item in phones[:15]:
        print(f"  {item['brand']:15} {item['model']:30} | IDs {item['min_id']:5}-{item['max_id']:5} | {item['count']:3} guides")
    
    print("\n" + "=" * 80)
    print("\nQUICK REFERENCE:")
    print("-" * 80)
    
    # Summary
    summary = await conn.fetch('''
        SELECT 
            CASE 
                WHEN category IN ('PC', 'Mac', 'Computer Hardware') THEN 'LAPTOP/COMPUTER'
                WHEN category = 'Phone' THEN 'PHONE'
                WHEN category = 'Tablet' THEN 'TABLET'
                ELSE 'OTHER'
            END as device_type,
            MIN(id) as start_id,
            MAX(id) as end_id,
            COUNT(*) as total
        FROM tutorials
        WHERE source = 'myfixit'
        GROUP BY device_type
        ORDER BY start_id
    ''')
    
    for s in summary:
        print(f"{s['device_type']:20} | Tutorial IDs: {s['start_id']:5} to {s['end_id']:5} | Total: {s['total']:5}")
    
    await conn.close()

asyncio.run(check_indices())
