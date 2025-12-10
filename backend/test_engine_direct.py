"""
Direct test of knowledge engine (bypasses API)
Shows exactly what the ML matching is doing
"""

import sys
sys.path.insert(0, 'E:\\z.code\\arvr\\backend')

from diagnosis.knowledge_engine import get_engine

def test_direct():
    print("\n" + "="*70)
    print("DIRECT KNOWLEDGE ENGINE TEST")
    print("="*70)
    
    # Get engine
    print("\nInitializing engine...")
    engine = get_engine()
    
    # Test cases
    test_cases = [
        "laptop won't turn on, no power",
        "overheating and fan loud",
        "battery not charging",
        "black screen no display",
        "computer does not start pressing power button"
    ]
    
    for symptoms in test_cases:
        print(f"\n{'='*70}")
        print(f"Testing: {symptoms}")
        print("="*70)
        
        best_match, alternatives = engine.diagnose(symptoms)
        
        if best_match:
            print(f"\n✅ MATCH FOUND!")
            print(f"   Issue: {best_match['issue_type']}")
            print(f"   Confidence: {best_match['confidence']:.2%}")
            print(f"   Similarity: {best_match['similarity_score']:.4f}")
            print(f"   Source: {best_match['source_file']}")
            print(f"   Steps: {len(best_match['solution_steps'])}")
            
            if best_match['solution_steps']:
                print(f"\n   First step: {best_match['solution_steps'][0][:100]}...")
            
            if alternatives:
                print(f"\n   Alternatives:")
                for alt in alternatives:
                    print(f"     - {alt['issue_type']} ({alt['confidence']:.2%})")
        else:
            print("\n❌ NO MATCH FOUND")

if __name__ == "__main__":
    test_direct()
