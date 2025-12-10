import asyncpg
import asyncio
import json

async def check_database():
    pool = await asyncpg.create_pool(
        'postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair'
    )
    
    async with pool.acquire() as conn:
        # Check total count
        count = await conn.fetchval('SELECT COUNT(*) FROM repair_procedures')
        print(f'Total tutorials in database: {count}')
        
        # Check sample tutorial
        tutorial = await conn.fetchrow(
            'SELECT * FROM repair_procedures LIMIT 1'
        )
        print(f'\nSample tutorial columns: {tutorial.keys()}')
        print(f'Sample tutorial data: {dict(tutorial)}')
        
        # Get all tutorials
        all_tutorials = await conn.fetch('SELECT id, device_model, issue, cause, source FROM repair_procedures')
        print(f'\nAll {len(all_tutorials)} tutorials:')
        for t in all_tutorials:
            print(f'  ID {t["id"]}: {t["device_model"]} - {t["issue"]} ({t["cause"]}) [{t["source"]}]')
    
    await pool.close()

asyncio.run(check_database())
