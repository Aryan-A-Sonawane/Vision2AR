import asyncpg
import asyncio

async def check_tutorials():
    pool = await asyncpg.create_pool(
        'postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair'
    )
    
    async with pool.acquire() as conn:
        count = await conn.fetchval('SELECT COUNT(*) FROM tutorials')
        print(f'Total tutorials: {count}')
        
        if count > 0:
            sample = await conn.fetch('SELECT id, brand, model, issue_type, title, source FROM tutorials LIMIT 10')
            print(f'\nSample tutorials:')
            for t in sample:
                print(f'  ID {t["id"]}: {t["brand"]} {t["model"]} - {t["issue_type"]} ({t["source"]})')
                print(f'       Title: {t["title"][:80]}...')
    
    await pool.close()

asyncio.run(check_tutorials())
