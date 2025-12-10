"""
Simple data verification - PostgreSQL focused
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.db_utils import (
    DatabaseConnection, get_stats, get_tutorial,
    search_tutorials_by_keywords, get_tutorials_by_brand
)

async def simple_verify():
    """Simple verification of seeded data"""
    
    print("=" * 60)
    print("Data Verification Report")
    print("=" * 60)
    
    # 1. Overall Statistics
    print("\n📊 OVERALL STATISTICS")
    print("-" * 60)
    stats = await get_stats()
    
    print(f"✓ Total Tutorials: {stats['total_tutorials']}")
    print(f"✓ Total Steps: {stats['total_steps']}")
    print(f"✓ Total Tools: {stats['total_tools']}")
    print(f"✓ Total Chat Sessions: {stats['total_sessions']}")
    
    # 2. By Brand
    print("\n📱 TUTORIALS BY BRAND")
    print("-" * 60)
    if stats['by_brand']:
        for item in stats['by_brand']:
            print(f"  {item['brand'].upper():10} {item['count']:3} tutorials")
    
    # 3. By Source
    print("\n📚 TUTORIALS BY SOURCE")
    print("-" * 60)
    if stats['by_source']:
        for item in stats['by_source']:
            print(f"  {item['source'].upper():10} {item['count']:3} tutorials")
    
    # 4. Sample Tutorials from Each Brand
    print("\n🔍 SAMPLE TUTORIALS")
    print("-" * 60)
    
    for brand in ['dell', 'lenovo', 'hp']:
        tutorials = await get_tutorials_by_brand(brand, limit=2)
        if tutorials:
            print(f"\n{brand.upper()}:")
            for t in tutorials[:2]:
                print(f"  • {t['title'][:70]}...")
                print(f"    Keywords: {', '.join(t['keywords'][:5])}")
                print(f"    Issue: {t['issue_type']} | Difficulty: {t['difficulty']}")
    
    # 5. Detailed Tutorial Example
    print("\n📖 DETAILED TUTORIAL EXAMPLE")
    print("-" * 60)
    
    dell_tutorials = await get_tutorials_by_brand('dell', limit=1)
    if dell_tutorials:
        tutorial = await get_tutorial(dell_tutorials[0]['id'])
        
        print(f"ID: {tutorial['id']}")
        print(f"Title: {tutorial['title']}")
        print(f"Brand: {tutorial['brand']}")
        print(f"Model: {tutorial['model']}")
        print(f"Issue Type: {tutorial['issue_type']}")
        print(f"Source: {tutorial['source']}")
        print(f"Difficulty: {tutorial['difficulty']}")
        print(f"Estimated Time: {tutorial['estimated_time_minutes']} min")
        print(f"\nKeywords ({len(tutorial['keywords'])}):")
        print(f"  {', '.join(tutorial['keywords'])}")
        print(f"\nSteps: {len(tutorial['steps'])}")
        for i, step in enumerate(tutorial['steps'][:3], 1):
            print(f"  {i}. {step['description'][:80]}...")
        
        if len(tutorial['steps']) > 3:
            print(f"  ... and {len(tutorial['steps']) - 3} more steps")
        
        if tutorial['warnings']:
            print(f"\nWarnings: {len(tutorial['warnings'])}")
            for w in tutorial['warnings'][:2]:
                print(f"  ⚠ [{w['severity']}] {w['warning_text'][:80]}...")
    
    # 6. Keyword Search Test
    print("\n🔎 KEYWORD SEARCH TEST")
    print("-" * 60)
    
    test_cases = [
        (['screen', 'black', 'display'], 'dell'),
        (['battery', 'power', 'charging'], 'lenovo'),
        (['overheating', 'fan', 'thermal'], 'hp')
    ]
    
    for keywords, brand in test_cases:
        results = await search_tutorials_by_keywords(keywords, brand=brand, limit=3)
        print(f"\nSearching {brand.upper()} for: {keywords}")
        print(f"Found: {len(results)} tutorials")
        for r in results[:2]:
            print(f"  • {r['title'][:60]}...")
    
    # 7. Issue Type Coverage
    print("\n🏷️  ISSUE TYPE COVERAGE")
    print("-" * 60)
    
    all_tutorials = []
    for brand in ['dell', 'lenovo', 'hp']:
        all_tutorials.extend(await get_tutorials_by_brand(brand, limit=100))
    
    issue_types = {}
    for t in all_tutorials:
        issue_type = t.get('issue_type', 'unknown')
        issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
    
    for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {issue_type:15} {count:3} tutorials")
    
    # 8. Data Quality Checks
    print("\n✅ DATA QUALITY CHECKS")
    print("-" * 60)
    
    # Count tutorials without keywords
    no_keywords = sum(1 for t in all_tutorials if not t.get('keywords'))
    
    # Count tutorials without steps
    no_steps_count = 0
    for t in all_tutorials:
        full = await get_tutorial(t['id'])
        if not full['steps']:
            no_steps_count += 1
    
    print(f"  Tutorials without keywords: {no_keywords}")
    print(f"  Tutorials without steps: {no_steps_count}")
    print(f"  Average steps per tutorial: {stats['total_steps'] / stats['total_tutorials']:.1f}")
    
    if no_keywords == 0 and no_steps_count == 0:
        print("\n  ✓ All data quality checks passed!")
    else:
        print("\n  ⚠ Some quality issues detected")
    
    # Final Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✓ {stats['total_tutorials']} tutorials loaded successfully")
    print(f"✓ {stats['total_steps']} steps across all tutorials")
    print(f"✓ {len(issue_types)} different issue types covered")
    print(f"✓ 3 brands: Dell, Lenovo, HP")
    print("\n🎉 Database seeding complete!")
    
    await DatabaseConnection.close_pool()

if __name__ == "__main__":
    asyncio.run(simple_verify())
