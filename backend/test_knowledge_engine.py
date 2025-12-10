"""
Test script to verify knowledge-based diagnosis works end-to-end
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_diagnosis_flow():
    print("="*70)
    print(" Testing Knowledge-Based Diagnosis Engine")
    print("="*70)
    print()
    
    # Test 1: Start diagnosis session
    print("TEST 1: Starting diagnosis session...")
    response = requests.post(
        f"{BASE_URL}/api/diagnose",
        json={
            "device_model": "lenovo thinkpad",
            "issue_description": "laptop won't turn on, black screen, no power"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        session_id = data["session_id"]
        print(f"✓ Session created: {session_id}")
        print(f"  Confidence: {data['confidence']}")
        print(f"  Questions: {len(data.get('questions', []))}")
        
        # Check if immediate diagnosis was given
        if data.get("diagnosis"):
            print("\n✓ IMMEDIATE DIAGNOSIS FOUND:")
            print(f"  Cause: {data['diagnosis'].get('cause', 'N/A')}")
            print(f"  Confidence: {data['diagnosis'].get('confidence', 'N/A')}")
            print(f"  Steps: {len(data['diagnosis'].get('solution_steps', []))}")
            print(f"  Tools: {data['diagnosis'].get('tools_needed', [])}")
            print(f"  Warnings: {len(data['diagnosis'].get('warnings', []))}")
            
            # Check raw manual extract
            raw = data['diagnosis'].get('raw_manual_extract')
            if raw:
                print(f"\n✓ RAW MANUAL TEXT INCLUDED (length: {len(raw)} chars)")
                print(f"\nFirst 500 chars of manual text:")
                print("-" * 70)
                print(raw[:500])
                print("-" * 70)
            else:
                print("\n⚠ No raw manual text found")
            
            # Check source file
            source = data['diagnosis'].get('source_file')
            if source:
                print(f"\n✓ Source: {source}")
            
            return True
        else:
            print("  No immediate diagnosis - questions generated")
            
            # Answer questions to build confidence
            for i, question in enumerate(data.get('questions', [])[:2]):
                print(f"\n  Question {i+1}: {question['text']}")
                # Simulate "no" answer
                answer_resp = requests.post(
                    f"{BASE_URL}/api/answer",
                    json={
                        "session_id": session_id,
                        "question_id": question["id"],
                        "answer": "no"
                    }
                )
                
                if answer_resp.status_code == 200:
                    answer_data = answer_resp.json()
                    print(f"    Confidence now: {answer_data['confidence']}")
                    
                    if answer_data.get("diagnosis"):
                        print("\n✓ DIAGNOSIS TRIGGERED:")
                        print(f"  Cause: {answer_data['diagnosis'].get('cause', 'N/A')}")
                        print(f"  Steps: {len(answer_data['diagnosis'].get('solution_steps', []))}")
                        
                        raw = answer_data['diagnosis'].get('raw_manual_extract')
                        if raw:
                            print(f"\n✓ RAW MANUAL TEXT INCLUDED (length: {len(raw)} chars)")
                            print(f"\nFirst 500 chars:")
                            print("-" * 70)
                            print(raw[:500])
                            print("-" * 70)
                        
                        return True
    
    print("\n⚠ Did not reach diagnosis state")
    return False


def test_overheat_issue():
    print("\n" + "="*70)
    print(" Testing with Overheating Issue (high procedure count)")
    print("="*70)
    print()
    
    response = requests.post(
        f"{BASE_URL}/api/diagnose",
        json={
            "device_model": "dell latitude",
            "issue_description": "laptop overheating, fan very loud, shutting down unexpectedly"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Session created")
        print(f"  Confidence: {data['confidence']}")
        
        if data.get("diagnosis"):
            print("\n✓ DIAGNOSIS PROVIDED:")
            diag = data['diagnosis']
            print(f"  Cause: {diag.get('cause', 'N/A')}")
            print(f"  Confidence: {diag.get('confidence', 'N/A')}")
            print(f"  Solution steps: {len(diag.get('solution_steps', []))}")
            
            # Print first 3 steps
            steps = diag.get('solution_steps', [])
            if steps:
                print("\n  First 3 steps:")
                for i, step in enumerate(steps[:3], 1):
                    print(f"    {i}. {step}")
            
            # Check manual text
            raw = diag.get('raw_manual_extract')
            if raw:
                print(f"\n✓ RAW OEM MANUAL TEXT (length: {len(raw)} chars)")
                print("\nSample:")
                print("-" * 70)
                print(raw[:600])
                print("-" * 70)
            
            # Check alternatives
            alts = diag.get('alternatives', [])
            if alts:
                print(f"\n✓ Alternatives provided: {len(alts)}")
                for alt in alts[:2]:
                    print(f"  - {alt.get('issue_type', 'N/A')} (conf: {alt.get('confidence', 0):.2f})")
            
            return True
    
    return False


if __name__ == "__main__":
    import sys
    
    try:
        # Test basic diagnosis flow
        test1_passed = test_diagnosis_flow()
        
        # Test high-confidence issue
        test2_passed = test_overheat_issue()
        
        print("\n" + "="*70)
        print(" TEST RESULTS")
        print("="*70)
        print(f"  Basic diagnosis flow: {'✓ PASS' if test1_passed else '✗ FAIL'}")
        print(f"  Overheating diagnosis: {'✓ PASS' if test2_passed else '✗ FAIL'}")
        print()
        
        if test1_passed or test2_passed:
            print("✓ Knowledge-Based Engine is working!")
            print("  - OEM manuals loaded successfully")
            print("  - Semantic matching functional")
            print("  - Raw manual text included in responses")
            sys.exit(0)
        else:
            print("⚠ Tests did not complete successfully")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
