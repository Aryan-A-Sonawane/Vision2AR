"""
Populate tutorial images from iFixit API

This script fetches image URLs from iFixit for existing tutorials
and updates the tutorial_steps table with actual CDN image URLs.
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_sources.ifixit_api import IFixitAPI


async def populate_images():
    """Fetch and populate images for tutorials from iFixit"""
    
    # Database connection
    DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:1234@localhost:5432/arvr")
    
    print("=" * 70)
    print("POPULATING TUTORIAL IMAGES FROM IFIXIT")
    print("=" * 70)
    
    conn = await asyncpg.connect(DB_URL)
    
    try:
        # Get tutorials that need images (source = ifixit)
        tutorials = await conn.fetch("""
            SELECT t.id, t.title, t.brand, t.model, t.source_id
            FROM tutorials t
            WHERE t.source = 'ifixit' 
            AND t.source_id IS NOT NULL
            LIMIT 10
        """)
        
        print(f"\n[INFO] Found {len(tutorials)} iFixit tutorials to process")
        
        if len(tutorials) == 0:
            print("\n[INFO] No iFixit tutorials found with source_id")
            print("[TIP] Make sure tutorials have source='ifixit' and source_id set")
            return
        
        ifixit = IFixitAPI()
        updated_count = 0
        
        for tutorial in tutorials:
            tutorial_id = tutorial['id']
            source_id = tutorial['source_id']
            title = tutorial['title']
            
            print(f"\n[{tutorial_id}] Processing: {title}")
            print(f"  iFixit Guide ID: {source_id}")
            
            try:
                # Fetch guide from iFixit
                guide = ifixit.get_guide(int(source_id))
                
                if not guide or 'steps' not in guide:
                    print(f"  ⚠️  No guide data found")
                    continue
                
                steps = guide['steps']
                print(f"  ✓ Found {len(steps)} steps with images")
                
                # Update each step with image URL
                for step_data in steps:
                    step_num = step_data.get('step_number', 0)
                    images = step_data.get('images', [])
                    
                    if images and len(images) > 0:
                        # Use the medium-sized image (good for web)
                        image_url = images[0].get('medium', images[0].get('standard', ''))
                        
                        if image_url:
                            # Update database
                            await conn.execute("""
                                UPDATE tutorial_steps
                                SET image_url = $1
                                WHERE tutorial_id = $2 AND step_number = $3
                            """, image_url, tutorial_id, step_num)
                            
                            print(f"    Step {step_num}: ✓ Image added")
                
                updated_count += 1
                print(f"  ✅ Updated tutorial {tutorial_id}")
                
            except Exception as e:
                print(f"  ❌ Error processing tutorial {tutorial_id}: {e}")
                continue
        
        print("\n" + "=" * 70)
        print(f"✅ Successfully updated {updated_count}/{len(tutorials)} tutorials")
        print("=" * 70)
        
        # Show sample results
        sample = await conn.fetch("""
            SELECT t.id, t.title, COUNT(ts.image_url) as images_count
            FROM tutorials t
            LEFT JOIN tutorial_steps ts ON t.id = ts.tutorial_id AND ts.image_url IS NOT NULL
            WHERE t.source = 'ifixit'
            GROUP BY t.id, t.title
            LIMIT 5
        """)
        
        print("\n📊 Sample results:")
        for row in sample:
            print(f"  [{row['id']}] {row['title']}: {row['images_count']} images")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    print("\n🖼️  Tutorial Image Population Script")
    print("This will fetch images from iFixit API and populate the database\n")
    
    asyncio.run(populate_images())
