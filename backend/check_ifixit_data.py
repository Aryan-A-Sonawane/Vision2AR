import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair')
    
    # Check iFixit tutorials
    tutorials = await conn.fetch(
        "SELECT id, title, source, source_id FROM tutorials WHERE source='ifixit' LIMIT 10"
    )
    print('\n=== iFixit Tutorials ===')
    for t in tutorials:
        print(f"{t['id']}: {t['title']} (source_id: {t['source_id']})")
    
    # Check their steps
    if tutorials:
        tutorial_id = tutorials[0]['id']
        print(f'\n=== Steps for Tutorial {tutorial_id} ===')
        steps = await conn.fetch(
            "SELECT step_number, LEFT(description, 100) as desc, image_url FROM tutorial_steps WHERE tutorial_id = $1 ORDER BY step_number",
            tutorial_id
        )
        for s in steps:
            print(f"Step {s['step_number']}: {s['desc']}...")
            print(f"  Image URL: {s['image_url']}")
    
    await conn.close()

asyncio.run(check())
