import asyncio
import asyncpg

async def show_categories():
    conn = await asyncpg.connect('postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair')
    
    print("\n=== ALL CATEGORIES IN MYFIXIT SOURCE ===\n")
    
    cats = await conn.fetch('''
        SELECT DISTINCT category 
        FROM tutorials 
        WHERE source = 'myfixit'
        ORDER BY category
    ''')
    
    for c in cats:
        print(f"  - {c['category']}")
    
    await conn.close()

asyncio.run(show_categories())
