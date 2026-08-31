#!/usr/bin/env python3
"""
Test Coordinator API - Pure HTTP requests, no database connection
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_api():
    print("="*80)
    print("COORDINATOR API HTTP TEST")
    print("="*80)
    
    # Wait for server
    print("\nWaiting for server...")
    for i in range(10):
        try:
            requests.get(f"{BASE_URL}/", timeout=2)
            print("✓ Server is ready!")
            break
        except:
            if i < 9:
                print(f"  Waiting... ({i+1}/10)")
                time.sleep(1)
            else:
                print("✗ Server not responding")
                return False
    
    # Test 1: I-code search
    print("\n" + "-"*80)
    print("TEST 1: Search for I-2607037 (I-code format)")
    print("-"*80)
    try:
        response = requests.post(
            f"{BASE_URL}/coordinator/api/search-employee",
            json={"employee_code": "I-2607037"},
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Body: {json.dumps(response.json(), indent=2)}")
        test1_pass = response.status_code in [200, 404]
        print(f"Result: {'PASS' if test1_pass else 'FAIL'}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        test1_pass = False
    
    # Test 2: E-code search
    print("\n" + "-"*80)
    print("TEST 2: Search for E-2606026 (E-code format)")
    print("-"*80)
    try:
        response = requests.post(
            f"{BASE_URL}/coordinator/api/search-employee",
            json={"employee_code": "E-2606026"},
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Body: {json.dumps(response.json(), indent=2)}")
        test2_pass = response.status_code in [200, 404]
        print(f"Result: {'PASS' if test2_pass else 'FAIL'}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        test2_pass = False
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Test 1 (I-2607037): {'PASS' if test1_pass else 'FAIL'}")
    print(f"Test 2 (E-2606026): {'PASS' if test2_pass else 'FAIL'}")
    
    return test1_pass and test2_pass

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
