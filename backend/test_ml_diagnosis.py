"""Test ML Diagnosis Flow"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_diagnosis_flow():
    print("=" * 60)
    print("Testing ML-Powered Diagnosis Flow")
    print("=" * 60)
    
    # Step 1: Start diagnosis
    print("\n1. Submitting symptoms...")
    symptoms_payload = {
        "device_model": "lenovo_ideapad_5",
        "issue_description": "My laptop won't turn on. The power LED doesn't light up and there's no fan noise."
    }
    
    response = requests.post(f"{BASE_URL}/api/diagnose", json=symptoms_payload)
    data = response.json()
    
    print(f"   Session ID: {data.get('session_id')}")
    print(f"   Confidence: {data.get('confidence', 0) * 100:.1f}%")
    
    if data.get('debug_info'):
        debug = data['debug_info']
        print(f"   Embedding Model: {debug.get('embedding_model')}")
        print(f"   Matches Found: {debug.get('matches_found')}")
        print(f"   Sources Used: {', '.join(debug.get('sources_used', []))}")
    
    session_id = data.get('session_id')
    
    # Check if immediate diagnosis or questions
    if data.get('diagnosis'):
        print("\n✓ Immediate Diagnosis Reached!")
        diagnosis = data['diagnosis']
        print(f"   Cause: {diagnosis['cause']}")
        print(f"   Easy Fix: {diagnosis['easy_fix']}")
        print(f"   Risk Level: {diagnosis['risk_level']}")
        print(f"   Tools Needed: {', '.join(diagnosis['tools_needed'])}")
        
        if diagnosis.get('source_breakdown'):
            print("\n   Source Contributions:")
            for source, contributions in diagnosis['source_breakdown'].items():
                print(f"     - {source}: {', '.join(contributions)}")
        
    elif data.get('questions'):
        questions = data['questions']
        print(f"\n2. ML Generated {len(questions)} questions:")
        
        # Answer first question
        q = questions[0]
        print(f"\n   Q1: {q['text']}")
        print(f"   Answer: no (simulating user response)")
        
        answer_payload = {
            "session_id": session_id,
            "question_id": q['id'],
            "answer": "no"
        }
        
        response = requests.post(f"{BASE_URL}/api/answer", json=answer_payload)
        data = response.json()
        
        print(f"   Updated Confidence: {data.get('confidence', 0) * 100:.1f}%")
        
        if data.get('debug_info', {}).get('belief_update'):
            print("   Belief Vector Updated ✓")
        
        if data.get('diagnosis'):
            print("\n✓ Final Diagnosis:")
            diagnosis = data['diagnosis']
            print(f"   Cause: {diagnosis['cause']}")
            print(f"   Easy Fix: {diagnosis['easy_fix']}")
            print(f"   Solution Steps:")
            for i, step in enumerate(diagnosis['solution_steps'], 1):
                print(f"     {i}. {step}")
            
            if diagnosis.get('source_breakdown'):
                print("\n   Source Breakdown:")
                for source, contributions in diagnosis['source_breakdown'].items():
                    print(f"     - {source}: {', '.join(contributions)}")
        
        elif data.get('next_question'):
            nq = data['next_question']
            print(f"\n   Next Question: {nq['text']}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_diagnosis_flow()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
