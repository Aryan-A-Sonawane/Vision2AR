"""
Migrate OEM manuals from knowledge_base_v2.json to new database
Store with source='oem'
"""
import asyncio
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from analysis.text_analyzer import TextAnalyzer
from database.db_utils import (
    DatabaseConnection, create_tutorial, add_tutorial_step,
    add_tutorial_tool, add_tutorial_warning, get_stats
)
from database.weaviate_utils import add_tutorial_to_weaviate
from sentence_transformers import SentenceTransformer

async def seed_oem_data():
    """Migrate OEM manuals to new database schema"""
    
    print("=" * 60)
    print("OEM Manual Migration")
    print("=" * 60)
    
    # Load knowledge base
    kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'knowledge_base_v2.json')
    
    if not os.path.exists(kb_path):
        print(f"✗ Knowledge base not found: {kb_path}")
        return
    
    print(f"\n[1] Loading knowledge base...")
    with open(kb_path, 'r', encoding='utf-8') as f:
        procedures = json.load(f)
    
    print(f"✓ Loaded {len(procedures)} procedures")
    
    # Initialize components
    print("\n[2] Initializing components...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    text_analyzer = TextAnalyzer(model)
    print("✓ Components initialized")
    
    # Track statistics
    total_added = 0
    failed = 0
    
    # Process each procedure
    print(f"\n[3] Migrating procedures...")
    
    for idx, proc in enumerate(procedures, 1):
        try:
            brand = proc.get('brand', 'dell').lower()
            issue_type = proc.get('issue_type', 'general')
            
            # Create title from issue type and symptoms
            symptoms = proc.get('symptoms', [])
            if symptoms:
                title = f"{brand.title()} - {issue_type.replace('_', ' ').title()}: {symptoms[0]}"
            else:
                title = f"{brand.title()} - {issue_type.replace('_', ' ').title()}"
            
            # Analyze text
            analysis_text = f"{title} {' '.join(symptoms)} {' '.join(proc.get('solution_steps', []))[:500]}"
            analysis = text_analyzer.analyze(analysis_text, brand)
            
            # Map issue type to category
            issue_type_map = {
                'no_boot': 'power',
                'battery_issue': 'power',
                'black_screen': 'display',
                'display_issue': 'display',
                'keyboard_issue': 'input',
                'overheating': 'thermal',
                'slow_performance': 'performance',
                'wifi_issue': 'network',
                'audio_issue': 'audio'
            }
            mapped_issue = issue_type_map.get(issue_type, issue_type)
            
            # Determine difficulty based on tools and warnings
            tools = proc.get('tools_needed', [])
            warnings = proc.get('warnings', [])
            
            if len(tools) > 5 or len(warnings) > 3:
                difficulty = 'hard'
            elif len(tools) > 2 or len(warnings) > 1:
                difficulty = 'medium'
            else:
                difficulty = 'easy'
            
            # Estimate time based on steps
            steps = proc.get('solution_steps', [])
            estimated_time = max(10, min(len(steps) * 5, 120))  # 5 min per step, cap at 120
            
            # Create tutorial
            tutorial_id = await create_tutorial(
                brand=brand,
                model='general',  # OEM manuals don't specify models
                issue_type=mapped_issue,
                title=title,
                keywords=analysis['keywords'],
                source='oem',
                difficulty=difficulty,
                estimated_time_minutes=estimated_time
            )
            
            print(f"  [{idx}/{len(procedures)}] Created tutorial {tutorial_id}: {title[:60]}...")
            
            # Add steps
            for step_num, step_text in enumerate(steps, 1):
                await add_tutorial_step(
                    tutorial_id=tutorial_id,
                    step_number=step_num,
                    description=step_text,
                    image_url=None,  # OEM manuals don't have image URLs
                    video_timestamp=None
                )
            
            # Add tools
            for tool in tools:
                if tool:  # Skip empty strings
                    await add_tutorial_tool(
                        tutorial_id=tutorial_id,
                        tool_name=tool,
                        tool_type='manual',
                        is_optional=False
                    )
            
            # Add warnings
            for warning in warnings:
                if warning:  # Skip empty strings
                    # Determine severity
                    severity = 'warning'
                    if any(word in warning.lower() for word in ['danger', 'critical', 'damage']):
                        severity = 'danger'
                    elif any(word in warning.lower() for word in ['note', 'info', 'tip']):
                        severity = 'info'
                    
                    await add_tutorial_warning(
                        tutorial_id=tutorial_id,
                        warning_text=warning,
                        severity=severity,
                        step_number=None
                    )
            
            # Add to Weaviate
            add_tutorial_to_weaviate(
                tutorial_id=tutorial_id,
                brand=brand,
                model='general',
                issue_type=mapped_issue,
                title=title,
                keywords=analysis['keywords'],
                source='oem',
                difficulty=difficulty,
                embedding=analysis['embedding']
            )
            
            total_added += 1
            
        except Exception as e:
            print(f"  [{idx}/{len(procedures)}] ✗ Error: {e}")
            failed += 1
            continue
    
    # Final statistics
    print("\n" + "=" * 60)
    print("Migration Complete")
    print("=" * 60)
    print(f"Total migrated: {total_added}")
    print(f"Failed: {failed}")
    
    # Get database stats
    stats = await get_stats()
    print(f"\nDatabase stats:")
    print(f"  Total tutorials: {stats['total_tutorials']}")
    print(f"  Total steps: {stats['total_steps']}")
    print(f"  Total tools: {stats['total_tools']}")
    
    if stats['by_source']:
        print("\n  By source:")
        for item in stats['by_source']:
            print(f"    - {item['source']}: {item['count']}")
    
    if stats['by_brand']:
        print("\n  By brand:")
        for item in stats['by_brand']:
            print(f"    - {item['brand']}: {item['count']}")
    
    await DatabaseConnection.close_pool()

if __name__ == "__main__":
    asyncio.run(seed_oem_data())
