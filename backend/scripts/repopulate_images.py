"""
Re-populate image URLs from myfixit JSON data.
This script reads the original myfixit JSON files and updates
tutorial_steps.image_url with the Images from the Steps array.
"""
import asyncio
import asyncpg
import json
from pathlib import Path

# Database configuration
DB_URL = "postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair"

# Path to myfixit data
MYFIXIT_PATH = Path(__file__).parent.parent / "data" / "myfixit"

async def repopulate_images():
    """Re-populate image URLs for myfixit tutorials"""
    conn = await asyncpg.connect(DB_URL)
    
    # Find all myfixit tutorials
    tutorials = await conn.fetch("""
        SELECT id, title, myfixit_guideid 
        FROM tutorials 
        WHERE source = 'myfixit' 
        AND myfixit_guideid IS NOT NULL
    """)
    
    print(f"\n=== Found {len(tutorials)} myfixit tutorials ===\n")
    
    # Load all JSON files from jsons/ directory
    jsons_dir = MYFIXIT_PATH / "jsons"
    if not jsons_dir.exists():
        print(f"ERROR: {jsons_dir} not found!")
        await conn.close()
        return
    
    # Read all category JSON files
    all_guides = []
    json_files = list(jsons_dir.glob("*.json"))
    print(f"Loading data from {len(json_files)} category files...")
    
    for json_file in json_files:
        print(f"  - {json_file.name}", end="")
        with open(json_file, 'r', encoding='utf-8') as f:
            # JSONL format - each line is a separate JSON object
            guides = []
            for line in f:
                line = line.strip()
                if line:
                    guides.append(json.loads(line))
            all_guides.extend(guides)
            print(f" ({len(guides)} guides)")
    
    print(f"\nTotal loaded: {len(all_guides)} guides\n")
    
    # Create a mapping: guideid -> guide data
    guides_by_id = {guide.get("Guidid"): guide for guide in all_guides}
    
    updated_count = 0
    images_added = 0
    
    for tutorial in tutorials:
        tutorial_id = tutorial['id']
        guideid = tutorial['myfixit_guideid']
        
        # Find matching guide in JSON
        guide = guides_by_id.get(guideid)
        if not guide:
            print(f"⚠️  Tutorial {tutorial_id} (guideid {guideid}): No matching guide in JSON")
            continue
        
        # Get steps from guide
        steps = guide.get("Steps", [])
        if not steps:
            continue
        
        tutorial_images = 0
        
        # Update each step with image URL
        for step_data in steps:
            # MyFixit uses Order field (0-indexed)
            step_order = step_data.get("Order", 0)
            step_number = step_order + 1  # Database uses 1-indexed
            
            # Get images array
            images = step_data.get("Images", [])
            if not images:
                continue
            
            # Get first image URL
            image_url = images[0]
            
            # Update database
            await conn.execute("""
                UPDATE tutorial_steps 
                SET image_url = $1
                WHERE tutorial_id = $2 
                AND step_number = $3
            """, image_url, tutorial_id, step_number)
            
            tutorial_images += 1
            images_added += 1
        
        if tutorial_images > 0:
            print(f"✅ Tutorial {tutorial_id}: {tutorial['title'][:60]}... ({tutorial_images} images)")
            updated_count += 1
    
    await conn.close()
    
    print(f"\n=== COMPLETE ===")
    print(f"Tutorials updated: {updated_count}")
    print(f"Total images added: {images_added}")
    print(f"\nTest now: http://localhost:3000/guides")

if __name__ == "__main__":
    asyncio.run(repopulate_images())
