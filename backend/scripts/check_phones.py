import asyncio
import asyncpg

async def check_phones():
    conn = await asyncpg.connect('postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair')
    
    print("\n=== CHECKING FOR PHONE TUTORIALS ===\n")
    
    # Check all categories
    all_cats = await conn.fetch('''
        SELECT DISTINCT category, COUNT(*) as cnt
        FROM tutorials
        WHERE source = 'myfixit'
        GROUP BY category
        ORDER BY category
    ''')
    
    print("All categories in myfixit source:")
    for cat in all_cats:
        print(f"  {cat['category']:30} - {cat['cnt']:5} tutorials")
    
    print("\n" + "=" * 80)
    print("\nSearching for phone-related tutorials...")
    
    phones = await conn.fetch('''
        SELECT id, brand, model, category, title
        FROM tutorials
        WHERE source = 'myfixit'
        AND (LOWER(category) LIKE '%phone%' 
             OR LOWER(brand) LIKE '%phone%'
             OR LOWER(model) LIKE '%phone%'
             OR LOWER(title) LIKE '%phone%')
        ORDER BY id
        LIMIT 20
    ''')
    
    if phones:
        print(f"\nFound {len(phones)} phone tutorials:")
        for p in phones:
            print(f"  ID {p['id']:5} | {p['category']:15} | {p['brand']:20} | {p['title'][:50]}")
    else:
        print("\n❌ No phone tutorials found in myfixit source")
        print("   The imported myfixit dataset only contains laptop/computer repair guides")
    
    await conn.close()

asyncio.run(check_phones())
