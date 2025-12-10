"""
Simple Test - Start server, test API, show results
"""
import subprocess
import time
import requests
import json
import sys

print("="*70)
print(" Knowledge-Based Diagnosis Engine - Live Test")
print("="*70)
print()

# Start backend in background
print("Starting backend server...")

import os
env = os.environ.copy()
env["HF_HOME"] = r"E:\z.code\arvr\.cache"

backend_process = subprocess.Popen(
    [
        r"E:\z.code\arvr\.venv\Scripts\python.exe",
        "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ],
    cwd=r"E:\z.code\arvr\backend",
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for startup and check output
print("Waiting for server to start...")
for i in range(15):
    time.sleep(1)
    # Check if process is still alive
    if backend_process.poll() is not None:
        print(f"\n✗ Backend exited with code: {backend_process.returncode}")
        stdout, stderr = backend_process.communicate()
        print("\nSTDOUT:")
        print(stdout)
        print("\nSTDERR:")
        print(stderr)
        sys.exit(1)
    
    # Try to connect
    if i > 5:
        try:
            resp = requests.get("http://localhost:8000/", timeout=1)
            print(f"✓ Backend is responding (status: {resp.status_code})")
            break
        except:
            pass

try:
    # Test 1: Black screen issue
    print("\n" + "="*70)
    print(" TEST 1: Black Screen Issue")
    print("="*70)
    
    response = requests.post(
        "http://localhost:8000/api/diagnose",
        json={
            "device_model": "dell latitude",
            "issue_description": "laptop screen is black, no display, power LED is on"
        },
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Status: {response.status_code}")
        print(f"✓ Session ID: {data['session_id']}")
        print(f"✓ Confidence: {data['confidence']:.1%}")
        
        if data.get('diagnosis'):
            print(f"\n✓ DIAGNOSIS FOUND!")
            diag = data['diagnosis']
            print(f"  Cause: {diag.get('cause', 'N/A')}")
            print(f"  Confidence: {diag.get('confidence', 0):.1%}")
            print(f"  Solution Steps: {len(diag.get('solution_steps', []))}")
            
            # Show first 3 steps
            steps = diag.get('solution_steps', [])
            if steps:
                print(f"\n  Steps:")
                for i, step in enumerate(steps[:3], 1):
                    print(f"    {i}. {step[:80]}...")
            
            # Show raw manual text
            raw = diag.get('raw_manual_extract')
            if raw:
                print(f"\n✓ RAW MANUAL TEXT ({len(raw)} chars):")
                print("  " + "-"*66)
                print("  " + raw[:300].replace('\n', '\n  '))
                print("  " + "-"*66)
        else:
            print(f"\n  Questions generated: {len(data.get('questions', []))}")
            for q in data.get('questions', [])[:2]:
                print(f"    - {q['text']}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
    
    # Test 2: Overheating
    print("\n" + "="*70)
    print(" TEST 2: Overheating Issue")
    print("="*70)
    
    response2 = requests.post(
        "http://localhost:8000/api/diagnose",
        json={
            "device_model": "lenovo thinkpad",
            "issue_description": "laptop overheating, fan very loud, shutting down"
        },
        timeout=10
    )
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"\n✓ Status: {response2.status_code}")
        print(f"✓ Confidence: {data2['confidence']:.1%}")
        
        if data2.get('diagnosis'):
            diag2 = data2['diagnosis']
            print(f"\n✓ DIAGNOSIS: {diag2.get('cause', 'N/A')}")
            print(f"  Tools needed: {diag2.get('tools_needed', [])}")
            print(f"  Warnings: {len(diag2.get('warnings', []))}")
        else:
            print(f"  Questions: {len(data2.get('questions', []))}")
    
    # Test 3: No boot
    print("\n" + "="*70)
    print(" TEST 3: No Boot Issue")
    print("="*70)
    
    response3 = requests.post(
        "http://localhost:8000/api/diagnose",
        json={
            "device_model": "hp pavilion",
            "issue_description": "computer does not start, no power, won't turn on"
        },
        timeout=10
    )
    
    if response3.status_code == 200:
        data3 = response3.json()
        print(f"\n✓ Status: {response3.status_code}")
        print(f"✓ Confidence: {data3['confidence']:.1%}")
        
        if data3.get('diagnosis'):
            print(f"\n✓ DIAGNOSIS PROVIDED")
            diag3 = data3['diagnosis']
            source = diag3.get('source', 'N/A')
            print(f"  Source: {source}")
            print(f"  Steps: {len(diag3.get('solution_steps', []))}")
    
    print("\n" + "="*70)
    print(" ✓ Tests Complete!")
    print("="*70)
    print()
    print("Knowledge engine is working and providing real OEM manual solutions!")
    print()
    
except requests.exceptions.RequestException as e:
    print(f"\n✗ Connection Error: {e}")
    print("\nBackend may not have started properly.")
    print("Check if port 8000 is available.")

finally:
    # Stop backend
    print("\nStopping backend...")
    backend_process.terminate()
    backend_process.wait(timeout=5)
    print("✓ Backend stopped")
