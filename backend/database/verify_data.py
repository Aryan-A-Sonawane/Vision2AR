"""
Verify seeded data in PostgreSQL and Weaviate
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.db_utils import (
    DatabaseConnection, get_stats, get_tutorial,
    search_tutorials_by_keywords, get_tutorials_by_brand
)
from database.weaviate_utils import (
    WeaviateConnection, get_weaviate_stats,
    search_similar_tutorials, search_by_keywords_and_vector
)
from sentence_transformers import SentenceTransformer

async def verify_data():
    """Verify data was seeded correctly"""
    
    print("=" * 60)
    print("Data Verification")
    print("=" * 60)
    
    # 1. PostgreSQL Statistics
    print("\n[1] PostgreSQL Statistics")
    print("-" * 60)
    stats = await get_stats()
    
    print(f"Total tutorials: {stats['total_tutorials']}")
    print(f"Total steps: {stats['total_steps']}")
    print(f"Total tools: {stats['total_tools']}")
    print(f"Total sessions: {stats['total_sessions']}")
    
    if stats['by_brand']:
        print("\nTutorials by brand:")
        for item in stats['by_brand']:
            print(f"  {item['brand']:10} {item['count']:3} tutorials")
    
    if stats['by_source']:
        print("\nTutorials by source:")
        for item in stats['by_source']:
            print(f"  {item['source']:10} {item['count']:3} tutorials")
    
    # 2. Weaviate Statistics
    print("\n[2] Weaviate Statistics")
    print("-" * 60)
    w_stats = get_weaviate_stats()
    print(f"Total tutorials: {w_stats['total_tutorials']}")
    print(f"Status: {w_stats['status']}")
    
    # 3. Sample Tutorial Check
    print("\n[3] Sample Tutorial Details")
    print("-" * 60)
    
    # Get first tutorial
    dell_tutorials = await get_tutorials_by_brand('dell', limit=1)
    if dell_tutorials:
        tutorial_id = dell_tutorials[0]['id']
        tutorial = await get_tutorial(tutorial_id)
        
        print(f"Tutorial ID: {tutorial['id']}")
        print(f"Title: {tutorial['title']}")
        print(f"Brand: {tutorial['brand']}")
        print(f"Model: {tutorial['model']}")
        print(f"Issue Type: {tutorial['issue_type']}")
        print(f"Source: {tutorial['source']}")
        print(f"Difficulty: {tutorial['difficulty']}")
        print(f"Estimated Time: {tutorial['estimated_time_minutes']} minutes")
        print(f"Keywords: {', '.join(tutorial['keywords'][:10])}")
        print(f"Steps: {len(tutorial['steps'])}")
        print(f"Tools: {len(tutorial['tools'])}")
        print(f"Warnings: {len(tutorial['warnings'])}")
        
        if tutorial['steps']:
            print(f"\nFirst step:")
            print(f"  {tutorial['steps'][0]['description'][:100]}...")
            if tutorial['steps'][0]['image_url']:
                print(f"  Image: {tutorial['steps'][0]['image_url']}")
    
    # 4. Keyword Search Test
    print("\n[4] Keyword Search Test")
    print("-" * 60)
    
    test_keywords = ['screen', 'black', 'display']
    print(f"Searching for keywords: {test_keywords}")
    
    results = await search_tutorials_by_keywords(test_keywords, brand='dell', limit=5)
    print(f"Found {len(results)} tutorials")
    
    for i, result in enumerate(results[:3], 1):
        print(f"  {i}. {result['title'][:60]}...")
        print(f"     Keywords: {', '.join(result['keywords'][:5])}")
    
    # 5. Vector Search Test
    print("\n[5] Vector Search Test")
    print("-" * 60)
    
    print("Loading sentence transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    test_query = "laptop screen is black but computer is running"
    print(f"Query: '{test_query}'")
    
    # Generate embedding
    query_embedding = model.encode(test_query)
    
    # Search Weaviate
    print("Searching Weaviate...")
    vector_results = search_similar_tutorials(query_embedding, brand='dell', limit=5)
    
    print(f"Found {len(vector_results)} similar tutorials")
    for i, result in enumerate(vector_results[:3], 1):
        print(f"  {i}. {result['title'][:60]}...")
        print(f"     Similarity: {result['similarity']:.2%}")
        print(f"     Brand: {result['brand']} | Source: {result['source']}")
    
    # 6. Hybrid Search Test
    print("\n[6] Hybrid Search Test (Vector + Keywords)")
    print("-" * 60)
    
    hybrid_results = search_by_keywords_and_vector(
        query_embedding=query_embedding,
        keywords=['screen', 'black', 'display', 'backlight'],
        brand='dell',
        limit=5
    )
    
    print(f"Found {len(hybrid_results)} tutorials")
    for i, result in enumerate(hybrid_results[:3], 1):
        print(f"  {i}. {result['title'][:60]}...")
        print(f"     Vector: {result['vector_score']:.2%} | Keyword: {result['keyword_score']:.2%} | Combined: {result['combined_score']:.2%}")
        print(f"     Keyword matches: {result['keyword_matches']}")
    
    # 7. Brand Coverage Check
    print("\n[7] Brand Coverage")
    print("-" * 60)
    
    for brand in ['dell', 'lenovo', 'hp']:
        brand_tutorials = await get_tutorials_by_brand(brand, limit=100)
        oem_count = sum(1 for t in brand_tutorials if t['source'] == 'oem')
        ifixit_count = sum(1 for t in brand_tutorials if t['source'] == 'ifixit')
        
        print(f"{brand.title():10} Total: {len(brand_tutorials):3} | OEM: {oem_count:3} | iFixit: {ifixit_count:3}")
    
    # 8. Data Consistency Check
    print("\n[8] Data Consistency")
    print("-" * 60)
    
    # Check if PostgreSQL and Weaviate counts match
    pg_count = stats['total_tutorials']
    wv_count = w_stats['total_tutorials']
    
    if pg_count == wv_count:
        print(f"✓ PostgreSQL and Weaviate counts match: {pg_count}")
    else:
        print(f"⚠ Count mismatch: PostgreSQL={pg_count}, Weaviate={wv_count}")
    
    # Check for tutorials without steps
    all_tutorials = await get_tutorials_by_brand('dell', limit=1000)
    all_tutorials += await get_tutorials_by_brand('lenovo', limit=1000)
    all_tutorials += await get_tutorials_by_brand('hp', limit=1000)
    
    no_keywords = sum(1 for t in all_tutorials if not t.get('keywords'))
    print(f"Tutorials without keywords: {no_keywords}")
    
    # Final Summary
    print("\n" + "=" * 60)
    print("Verification Complete")
    print("=" * 60)
    
    if pg_count > 0 and pg_count == wv_count and no_keywords == 0:
        print("✓ All checks passed!")
        print(f"✓ {pg_count} tutorials successfully seeded")
        print("✓ Both databases are in sync")
        print("✓ All tutorials have keywords")
    else:
        print("⚠ Some issues detected - review output above")
    
    await DatabaseConnection.close_pool()
    WeaviateConnection.close_client()

if __name__ == "__main__":
    asyncio.run(verify_data())
