"""
Test script for ML Diagnosis Engine V2
Verifies all ML components are working
"""

import asyncio
import sys
sys.path.insert(0, 'E:/z.code/arvr/backend')

from diagnosis.ml_engine_v2 import MLDiagnosisEngineV2, MultiModalInput


async def test_ml_engine():
    print("=" * 60)
    print("Testing ML Diagnosis Engine V2")
    print("=" * 60)
    
    # Initialize engine
    print("\n1. Initializing ML engine...")
    try:
        engine = MLDiagnosisEngineV2()
        print("   ✓ ML engine initialized")
        print(f"   ✓ Text model: {engine.text_model}")
        print(f"   ✓ LLM available: {engine.llm_available}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return
    
    # Test text analysis
    print("\n2. Testing text symptom analysis...")
    try:
        mm_input = MultiModalInput(
            text="My laptop won't turn on at all. No lights, no sounds, nothing happens when I press power button.",
            images=None,
            video_path=None
        )
        
        next_q, diagnosis, debug = await engine.start_diagnosis(
            device_model="lenovo_ideapad_5",
            initial_input=mm_input
        )
        
        print(f"   ✓ Text analysis complete")
        print(f"   ✓ Text analysis found: {debug.get('text_analysis', {}).get('key_symptoms', [])}")
        print(f"   ✓ Confidence: {debug.get('combined_confidence', 0.0):.0%}")
        print(f"   ✓ Generated question: {next_q.get('text', '')[:80]}...")
        
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test answer processing
    print("\n3. Testing answer processing...")
    try:
        conversation_history = [
            {"role": "user", "content": mm_input.text},
            {"role": "assistant", "content": next_q.get('text', '')}
        ]
        
        answer_text = "When I press the power button, I see a white LED light up for about 2 seconds, then it goes off. I don't hear any fan spinning."
        
        next_q2, diagnosis2, debug2 = await engine.process_answer(
            session_id="test-session",
            answer_text=answer_text,
            media=None,
            conversation_history=conversation_history,
            current_understanding=debug.get('combined_confidence', {})
        )
        
        print(f"   ✓ Answer processed")
        print(f"   ✓ Updated confidence: {debug2.get('updated_confidence', 0.0):.0%}")
        print(f"   ✓ Top cause: {debug2.get('top_cause', 'unknown')}")
        
        if diagnosis2:
            print(f"   ✓ Diagnosis ready: {diagnosis2.cause}")
        else:
            print(f"   ✓ Next question: {next_q2.get('text', '')[:80]}...")
        
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("✓ All ML components working!")
    print("=" * 60)
    print("\nReady to start backend with: python main_v2.py")
    print("Then access UI at: http://localhost:3000/diagnose-ml")


if __name__ == "__main__":
    asyncio.run(test_ml_engine())
