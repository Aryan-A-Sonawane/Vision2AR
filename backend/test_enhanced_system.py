"""
Test Enhanced Diagnostic System
"""
import asyncio
import asyncpg
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_belief_engine():
    """Test belief engine initialization and belief computation"""
    print("\n" + "="*70)
    print("TEST 1: Belief Engine")
    print("="*70)
    
    # Create database connection
    db_url = "postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair"
    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=2)
    
    try:
        from diagnosis.belief_engine import BeliefEngine
        
        engine = BeliefEngine(pool)
        print("✅ BeliefEngine initialized")
        
        # Test belief initialization
        symptoms = ["blue_screen", "error_0x007B"]
        visual_symptoms = []
        category = "PC"
        
        beliefs = await engine.initialize_beliefs(symptoms, visual_symptoms, category)
        
        print(f"\n✅ Belief vector computed:")
        for cause, prob in list(beliefs.items())[:5]:
            print(f"   {cause}: {prob:.3f}")
        
        # Test question selection
        question = await engine.select_next_question(
            current_beliefs=beliefs,
            processed_input={
                "symptoms": symptoms,
                "visual_symptoms": visual_symptoms,
                "brand": "lenovo",
                "brand_confidence": 0.95,
                "category": category
            },
            asked_questions=[],
            category=category
        )
        
        if question:
            print(f"\n✅ Question selected: {question.get('text', question.get('id'))}")
        else:
            print(f"\n⚠️ No questions available")
        
        print("\n✅ Test 1 PASSED")
        
    finally:
        await pool.close()


async def test_input_processor():
    """Test input processor with text"""
    print("\n" + "="*70)
    print("TEST 2: Input Processor")
    print("="*70)
    
    db_url = "postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair"
    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=2)
    
    try:
        from analysis.input_processor import InputProcessor
        
        processor = InputProcessor(pool)
        print("✅ InputProcessor initialized")
        
        # Test text processing
        text = "My Lenovo IdeaPad 5 shows blue screen with error 0x007B"
        result = await processor.process_text(text)
        
        print(f"\n✅ Text processed:")
        print(f"   Brand: {result['brand']} (confidence: {result['brand_confidence']})")
        print(f"   Category: {result['category']}")
        print(f"   Symptoms: {result['symptoms']}")
        print(f"   Error codes: {result['error_codes']}")
        
        print("\n✅ Test 2 PASSED")
        
    finally:
        await pool.close()


async def test_tutorial_matcher():
    """Test tutorial matcher"""
    print("\n" + "="*70)
    print("TEST 3: Tutorial Matcher")
    print("="*70)
    
    db_url = "postgresql://postgres:9850044547@localhost:5432/ar_laptop_repair"
    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=2)
    
    try:
        from analysis.tutorial_matcher import TutorialMatcher
        import weaviate
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Initialize Weaviate
        weaviate_url = os.getenv("WEAVIATE_URL")
        weaviate_key = os.getenv("WEAVIATE_API_KEY")
        
        weaviate_client = weaviate.Client(
            url=weaviate_url,
            auth_client_secret=weaviate.AuthApiKey(api_key=weaviate_key)
        )
        
        matcher = TutorialMatcher(pool, weaviate_client)
        print("✅ TutorialMatcher initialized")
        
        # Test hybrid search
        tutorials = await matcher.search_tutorials_hybrid(
            diagnosis="storage_driver_issue",
            symptoms=["blue_screen", "error_0x007B"],
            keywords=["blue", "screen", "error", "boot"],
            category="PC",
            brand="lenovo",
            limit=3
        )
        
        print(f"\n✅ Matched {len(tutorials)} tutorials:")
        for t in tutorials:
            print(f"   [{t['tutorial_id']}] {t['title']} - {t.get('final_score', 0):.3f}")
        
        print("\n✅ Test 3 PASSED")
        
    finally:
        await pool.close()


async def main():
    """Run all tests"""
    print("\n" + "#"*70)
    print("# ENHANCED DIAGNOSTIC SYSTEM - INTEGRATION TESTS")
    print("#"*70)
    
    try:
        await test_belief_engine()
        await test_input_processor()
        await test_tutorial_matcher()
        
        print("\n" + "#"*70)
        print("# ALL TESTS PASSED ✅")
        print("#"*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
