"""
Live Testing Script for Knowledge-Based Diagnosis Engine
Run this to see real-time diagnosis output
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def test_diagnosis(device_model, issue_description, test_name):
    """Test single diagnosis scenario"""
    print_header(f"TEST: {test_name}")
    
    print(f"\n📱 Device: {device_model}")
    print(f"❗ Issue: {issue_description}")
    print("\n⏳ Sending request to diagnosis engine...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/diagnose",
            json={
                "device_model": device_model,
                "issue_description": issue_description
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"\n❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        # Show results
        print(f"\n✅ Response received!")
        print(f"Session ID: {data['session_id']}")
        print(f"Confidence: {data['confidence']:.2%}")
        
        # Check if immediate diagnosis
        if data.get('diagnosis'):
            print("\n" + "🎯"*35)
            print("DIAGNOSIS PROVIDED")
            print("🎯"*35)
            
            diag = data['diagnosis']
            print(f"\n📋 Cause: {diag.get('cause', 'N/A')}")
            print(f"📊 Confidence: {diag.get('confidence', 0):.2%}")
            
            # Solution steps
            steps = diag.get('solution_steps', [])
            if steps:
                print(f"\n🔧 SOLUTION STEPS ({len(steps)} total):")
                for i, step in enumerate(steps[:5], 1):
                    print(f"   {i}. {step[:100]}{'...' if len(step) > 100 else ''}")
                if len(steps) > 5:
                    print(f"   ... and {len(steps) - 5} more steps")
            
            # Tools needed
            tools = diag.get('tools_needed', [])
            if tools:
                print(f"\n🛠️  TOOLS NEEDED: {', '.join(tools[:3])}")
            
            # Raw manual extract
            raw = diag.get('raw_manual_extract', '')
            if raw:
                print(f"\n📖 RAW OEM MANUAL TEXT:")
                print("   " + "-"*66)
                preview = raw[:300].replace('\n', ' ')
                print(f"   {preview}...")
                print(f"   [Total length: {len(raw)} characters]")
                print("   " + "-"*66)
            else:
                print("\n⚠️  No raw manual text included")
            
            # Source
            source = diag.get('source_file', 'N/A')
            print(f"\n📁 Source: {source}")
            
            # Alternatives
            alts = diag.get('alternative_causes', [])
            if alts:
                print(f"\n🔄 ALTERNATIVE DIAGNOSES:")
                for alt in alts[:3]:
                    print(f"   - {alt.get('cause', 'N/A')} ({alt.get('confidence', 0):.1%})")
            
            return True
        
        # Questions generated instead
        elif data.get('questions'):
            print("\n" + "❓"*35)
            print("FOLLOW-UP QUESTIONS GENERATED")
            print("❓"*35)
            
            questions = data['questions']
            print(f"\n{len(questions)} question(s) need to be answered:\n")
            for i, q in enumerate(questions, 1):
                print(f"{i}. {q['text']}")
                print(f"   Type: {q.get('type', 'unknown')}")
                if q.get('context'):
                    print(f"   Context: {q['context']}")
                print()
            
            return True
        
        else:
            print("\n⚠️  No diagnosis or questions returned")
            return False
    
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend")
        print("   Make sure backend is running on http://localhost:8000")
        return False
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "🚀"*35)
    print("  AR LAPTOP TROUBLESHOOTER - DIAGNOSIS ENGINE TEST")
    print("🚀"*35)
    print("\nTesting knowledge-based diagnosis with OEM manuals...")
    print("Backend URL:", BASE_URL)
    
    # Check if backend is running
    print("\n⏳ Checking backend status...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is online and ready!")
        else:
            print(f"⚠️  Backend responded with status {response.status_code}")
    except:
        print("❌ Backend is not responding!")
        print("   Please start the backend first:")
        print("   cd E:\\z.code\\arvr\\backend")
        print("   python main.py")
        return
    
    # Run test cases
    test_cases = [
        {
            "name": "No Boot Issue",
            "device": "Dell Latitude",
            "issue": "laptop won't turn on, pressing power button does nothing, no lights"
        },
        {
            "name": "Overheating Problem",
            "device": "Lenovo ThinkPad",
            "issue": "laptop overheating, fan very loud, shutting down unexpectedly"
        },
        {
            "name": "Battery Issue",
            "device": "HP Pavilion",
            "issue": "battery not charging, power adapter connected but battery stays at 0%"
        },
        {
            "name": "Black Screen",
            "device": "Dell XPS",
            "issue": "laptop turns on but screen stays black, can hear fan running"
        }
    ]
    
    results = []
    
    for test in test_cases:
        result = test_diagnosis(
            device_model=test["device"],
            issue_description=test["issue"],
            test_name=test["name"]
        )
        results.append((test["name"], result))
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed\n")
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {name}")
    
    print("\n" + "="*70)
    
    if passed == total:
        print("\n🎉 All tests passed! Knowledge-based diagnosis is working!")
    elif passed > 0:
        print(f"\n⚠️  {passed} out of {total} tests passed. Some issues detected.")
    else:
        print("\n❌ All tests failed. Check backend logs for errors.")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
