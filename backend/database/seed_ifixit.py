"""
Seed database with iFixit tutorials
Fetch 30 problems × 3 brands (Dell, Lenovo, HP) = 90 tutorials
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data_sources.ifixit_api import IFixitAPI
from analysis.text_analyzer import TextAnalyzer
from database.db_utils import (
    DatabaseConnection, create_tutorial, add_tutorial_step,
    add_tutorial_tool, add_tutorial_warning, get_stats
)
from database.weaviate_utils import add_tutorial_to_weaviate
from sentence_transformers import SentenceTransformer

# Common laptop problems to search for
COMMON_PROBLEMS = [
    # Display issues
    "screen replacement", "lcd replacement", "display not working",
    "backlight repair", "cracked screen", "dim display",
    
    # Power issues
    "battery replacement", "not charging", "power button",
    "dc jack repair", "no power",
    
    # Thermal issues
    "fan replacement", "overheating", "thermal paste",
    "cooling system", "loud fan",
    
    # Storage
    "hard drive replacement", "ssd upgrade", "storage upgrade",
    
    # Memory
    "ram upgrade", "memory replacement",
    
    # Input devices
    "keyboard replacement", "touchpad repair", "trackpad",
    
    # Connectivity
    "wifi card replacement", "bluetooth repair",
    
    # Audio
    "speaker replacement", "no sound",
    
    # Other
    "motherboard repair", "bios reset", "cmos battery"
]

BRANDS = ["Dell", "Lenovo", "HP"]

async def seed_ifixit_data():
    """Main seeding function"""
    
    print("=" * 60)
    print("iFixit Data Seeding")
    print("=" * 60)
    
    # Initialize components
    print("\n[1] Initializing components...")
    ifixit = IFixitAPI()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    text_analyzer = TextAnalyzer(model)
    
    print("✓ Components initialized")
    
    # Track statistics
    total_added = 0
    failed = 0
    skipped = 0
    
    # Process each brand
    for brand in BRANDS:
        print(f"\n[2] Processing {brand} tutorials...")
        brand_count = 0
        problems_per_brand = 30
        
        for problem in COMMON_PROBLEMS:
            if brand_count >= problems_per_brand:
                break
            
            query = f"{brand} laptop {problem}"
            print(f"  Searching: {query}")
            
            try:
                # Search for guides
                results = ifixit.search_device(query, device_type="laptop")
                
                if not results:
                    print(f"    ⚠ No results found")
                    continue
                
                # Get first matching guide
                for result in results[:2]:  # Try top 2 results
                    if brand_count >= problems_per_brand:
                        break
                    
                    # Check if it's a guide
                    if result.get("type") != "guide":
                        continue
                    
                    guide_id = result.get("guideid")
                    if not guide_id:
                        continue
                    
                    print(f"    Fetching guide {guide_id}...")
                    guide = ifixit.get_guide(guide_id)
                    
                    if not guide or not guide.get("steps"):
                        print(f"    ⚠ Invalid guide data")
                        continue
                    
                    # Analyze text
                    analysis_text = f"{guide['title']} {guide.get('device', '')} {problem}"
                    analysis = text_analyzer.analyze(analysis_text, brand.lower())
                    
                    # Determine issue type
                    issue_type = "general"
                    if analysis['symptom_categories']:
                        issue_type = analysis['symptom_categories'][0]
                    
                    # Map difficulty
                    difficulty_map = {
                        "Easy": "easy",
                        "Moderate": "medium",
                        "Difficult": "hard",
                        "Very difficult": "hard"
                    }
                    difficulty = difficulty_map.get(guide.get('difficulty', 'Moderate'), 'medium')
                    
                    # Parse time (e.g., "30 minutes - 1 hour" -> 30)
                    time_str = guide.get('time_required', '30 minutes')
                    estimated_time = 30
                    if 'hour' in time_str.lower():
                        estimated_time = 60
                    elif 'minute' in time_str.lower():
                        import re
                        match = re.search(r'(\d+)', time_str)
                        if match:
                            estimated_time = int(match.group(1))
                    
                    # Create tutorial in PostgreSQL
                    try:
                        tutorial_id = await create_tutorial(
                            brand=brand.lower(),
                            model=guide.get('device', '').replace(brand, '').strip(),
                            issue_type=issue_type,
                            title=guide['title'],
                            keywords=analysis['keywords'],
                            source='ifixit',
                            difficulty=difficulty,
                            estimated_time_minutes=estimated_time
                        )
                        
                        print(f"    ✓ Created tutorial {tutorial_id}: {guide['title']}")
                        
                        # Add steps
                        for step in guide['steps']:
                            await add_tutorial_step(
                                tutorial_id=tutorial_id,
                                step_number=step['step_number'],
                                description=step['description'],
                                image_url=step.get('image_url'),
                                video_timestamp=None
                            )
                        
                        print(f"      Added {len(guide['steps'])} steps")
                        
                        # Add tools
                        for tool in guide.get('tools', []):
                            tool_name = tool.get('text', '') if isinstance(tool, dict) else str(tool)
                            if tool_name:
                                await add_tutorial_tool(
                                    tutorial_id=tutorial_id,
                                    tool_name=tool_name,
                                    tool_type='manual',
                                    is_optional=False
                                )
                        
                        if guide.get('tools'):
                            print(f"      Added {len(guide['tools'])} tools")
                        
                        # Add warnings (from conclusion or general safety)
                        if guide.get('conclusion'):
                            await add_tutorial_warning(
                                tutorial_id=tutorial_id,
                                warning_text=guide['conclusion'][:500],
                                severity='info',
                                step_number=None
                            )
                        
                        # Add to Weaviate
                        add_tutorial_to_weaviate(
                            tutorial_id=tutorial_id,
                            brand=brand.lower(),
                            model=guide.get('device', '').replace(brand, '').strip(),
                            issue_type=issue_type,
                            title=guide['title'],
                            keywords=analysis['keywords'],
                            source='ifixit',
                            difficulty=difficulty,
                            embedding=analysis['embedding']
                        )
                        
                        print(f"      ✓ Added to Weaviate")
                        
                        total_added += 1
                        brand_count += 1
                        
                        # Small delay to avoid rate limiting
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        print(f"    ✗ Error creating tutorial: {e}")
                        failed += 1
                        continue
                    
            except Exception as e:
                print(f"    ✗ Search error: {e}")
                failed += 1
                continue
        
        print(f"\n  {brand}: Added {brand_count} tutorials")
    
    # Final statistics
    print("\n" + "=" * 60)
    print("Seeding Complete")
    print("=" * 60)
    print(f"Total added: {total_added}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    
    # Get database stats
    stats = await get_stats()
    print(f"\nDatabase stats:")
    print(f"  Total tutorials: {stats['total_tutorials']}")
    print(f"  Total steps: {stats['total_steps']}")
    print(f"  Total tools: {stats['total_tools']}")
    
    await DatabaseConnection.close_pool()

if __name__ == "__main__":
    asyncio.run(seed_ifixit_data())
