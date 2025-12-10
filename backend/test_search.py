import asyncpg
import asyncio
import sys
sys.path.append('E:\\z.code\\arvr\\backend')

from analysis.tutorial_matcher import TutorialMatcher

async def test_search():
    pool = await asyncpg.create_pool(
        'postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair'
    )
    
    matcher = TutorialMatcher(pool)
    
    print("Testing hybrid search...")
    results = await matcher.search_tutorials_hybrid(
        diagnosis="unknown",
        symptoms=["fan_noise"],
        keywords=["laptop", "making", "noise", "lenovo"],
        category="PC",
        brand="lenovo",
        limit=5
    )
    
    print(f"\nResults: {len(results)} tutorials found")
    for r in results:
        print(f"  ID {r.get('id', r.get('tutorial_id'))}: {r['title'][:80]}...")
        print(f"       Score: {r.get('final_score', r.get('hybrid_score', 0)):.3f}")
    
    await pool.close()

asyncio.run(test_search())
