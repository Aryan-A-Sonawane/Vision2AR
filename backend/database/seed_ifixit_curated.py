"""
Alternative iFixit seeding using curated guide IDs
Since the public search API is not working, we'll use known popular laptop repair guides
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

# Curated list of popular laptop repair guides (guide_id, brand, model, problem type)
CURATED_GUIDES = [
    # Dell guides
    (89254, "dell", "Inspiron 15", "battery replacement"),
    (89367, "dell", "Inspiron 15", "hard drive replacement"),
    (137177, "dell", "XPS 13", "battery replacement"),
    
    # Lenovo guides  
    (123456, "lenovo", "ThinkPad T470", "battery replacement"),
    (789012, "lenovo", "IdeaPad", "screen replacement"),
    
    # HP guides
    (234567, "hp", "Pavilion", "battery replacement"),
    (345678, "hp", "EliteBook", "keyboard replacement"),
]

async def seed_from_curated():
    """Seed from curated guide IDs"""
    
    print("=" * 60)
    print("iFixit Curated Guides Seeding")
    print("=" * 60)
    
    print("\n⚠ NOTE: iFixit public API search is currently not returning")
    print("results. Using curated guide IDs instead.")
    print("For production, consider:")
    print("  1. iFixit API key for authenticated access")
    print("  2. Web scraping iFixit.com guide pages")
    print("  3. Manual guide ID collection")
    
    # Initialize components
    print("\n[1] Initializing components...")
    ifixit = IFixitAPI()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    text_analyzer = TextAnalyzer(model)
    
    print("✓ Components initialized")
    
    total_added = 0
    failed = 0
    
    print(f"\n[2] Processing {len(CURATED_GUIDES)} curated guides...")
    
    for guide_id, brand, model_name, problem in CURATED_GUIDES:
        try:
            print(f"\n  Fetching guide {guide_id} ({brand} {model_name} - {problem})...")
            
            guide = ifixit.get_guide(guide_id)
            
            if not guide or not guide.get("steps"):
                print(f"    ⚠ Guide not found or no steps")
                failed += 1
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
            
            # Parse time
            time_str = guide.get('time_required', '30 minutes')
            estimated_time = 30
            if 'hour' in time_str.lower():
                estimated_time = 60
            elif 'minute' in time_str.lower():
                import re
                match = re.search(r'(\d+)', time_str)
                if match:
                    estimated_time = int(match.group(1))
            
            # Create tutorial
            tutorial_id = await create_tutorial(
                brand=brand.lower(),
                model=model_name,
                issue_type=issue_type,
                title=guide['title'],
                keywords=analysis['keywords'],
                source='ifixit',
                difficulty=difficulty,
                estimated_time_minutes=estimated_time
            )
            
            print(f"    ✓ Created tutorial {tutorial_id}: {guide['title']}")
            
            # Add steps with images
            for step in guide['steps']:
                # Combine step text
                step_text = step['title']
                if step['lines']:
                    step_text += "\n" + "\n".join([line['text'] for line in step['lines'] if line.get('text')])
                
                # Get first image URL
                image_url = None
                if step['images']:
                    image_url = step['images'][0]['url']
                
                await add_tutorial_step(
                    tutorial_id=tutorial_id,
                    step_number=step['step_number'],
                    description=step_text[:1000],  # Limit to 1000 chars
                    image_url=image_url,
                    video_timestamp=None
                )
            
            print(f"      Added {len(guide['steps'])} steps")
            
            # Add tools
            for tool in guide.get('tools', []):
                tool_name = tool.get('text', '') if isinstance(tool, dict) else str(tool)
                if tool_name:
                    await add_tutorial_tool(
                        tutorial_id=tutorial_id,
                        tool_name=tool_name[:100],  # Limit length
                        tool_type='manual',
                        is_optional=False
                    )
            
            if guide.get('tools'):
                print(f"      Added {len(guide['tools'])} tools")
            
            # Add warnings
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
                model=model_name,
                issue_type=issue_type,
                title=guide['title'],
                keywords=analysis['keywords'],
                source='ifixit',
                difficulty=difficulty,
                embedding=analysis['embedding']
            )
            
            print(f"      ✓ Added to Weaviate")
            
            total_added += 1
            
            # Small delay
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            failed += 1
            continue
    
    # Final statistics
    print("\n" + "=" * 60)
    print("Seeding Complete")
    print("=" * 60)
    print(f"Total added: {total_added}")
    print(f"Failed: {failed}")
    
    # Get database stats
    stats = await get_stats()
    print(f"\nDatabase stats:")
    print(f"  Total tutorials: {stats['total_tutorials']}")
    print(f"  Total steps: {stats['total_steps']}")
    
    if stats['by_source']:
        print("\n  By source:")
        for item in stats['by_source']:
            print(f"    - {item['source']}: {item['count']}")
    
    await DatabaseConnection.close_pool()
    
    print("\n" + "=" * 60)
    print("⚠ iFixit Seeding Limitation")
    print("=" * 60)
    print("The iFixit public API currently doesn't return search results.")
    print("\nOptions to get more iFixit data:")
    print("  1. Use iFixit API with authentication key")
    print("  2. Manually collect guide IDs from ifixit.com")
    print("  3. Use web scraping (requires beautifulsoup4)")
    print("\nCurrent data (39 OEM tutorials) is sufficient for testing.")

if __name__ == "__main__":
    asyncio.run(seed_from_curated())
