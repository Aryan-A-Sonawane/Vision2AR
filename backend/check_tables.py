import asyncpg
import asyncio

async def check_tables():
    pool = await asyncpg.create_pool(
        'postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair'
    )
    
    async with pool.acquire() as conn:
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        print(f'Tables in database:')
        for t in tables:
            print(f'  - {t["table_name"]}')
            
        # Check repair_procedures structure
        print(f'\nrepair_procedures columns:')
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'repair_procedures'
        """)
        for c in columns:
            print(f'  - {c["column_name"]}: {c["data_type"]}')
    
    await pool.close()

asyncio.run(check_tables())
