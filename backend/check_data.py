import asyncio
import asyncpg
import json

async def check_database():
    conn = await asyncpg.connect('postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair')
    
    # Check first step from tutorial 1
    print("\n=== CHECKING TUTORIAL STEP DATA ===\n")
    row = await conn.fetchrow(
        'SELECT * FROM tutorial_steps WHERE tutorial_id = 1 ORDER BY step_number LIMIT 1'
    )
    
    if row:
        print("Step 1 columns and data:")
        for key, value in dict(row).items():
            if isinstance(value, str) and len(value) > 150:
                print(f"  {key}: {value[:150]}...")
            else:
                print(f"  {key}: {value}")
    
    # Check all steps for tutorial 1
    print("\n=== ALL STEPS FOR TUTORIAL 1 ===\n")
    steps = await conn.fetch(
        'SELECT step_number, title, LEFT(description, 100) as desc_preview, image_url FROM tutorial_steps WHERE tutorial_id = 1 ORDER BY step_number'
    )
    
    for step in steps:
        print(f"Step {step['step_number']}: {step['title']}")
        print(f"  Description: {step['desc_preview']}...")
        print(f"  Image URL: {step['image_url']}")
        print()
    
    await conn.close()

asyncio.run(check_database())
