#!/usr/bin/env python3
"""
Test Coordinator API Endpoint
Tests both I-codes and E-codes for the search-employee endpoint
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
ENDPOINT = "/coordinator/api/search-employee"

def test_employee_search(employee_code):
    """Test the search-employee endpoint with a given employee code"""
    
    url = f"{BASE_URL}{ENDPOINT}"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "employee_code": employee_code
    }
    
    print("\n" + "="*80)
    print(f"Testing: {employee_code}")
    print("="*80)
    print(f"URL: {url}")
    print(f"Method: POST")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Body: {json.dumps(payload, indent=2)}")
    print("-"*80)
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print(f"\nResponse Body:")
        print(json.dumps(response.json(), indent=2))
        
        return {
            "employee_code": employee_code,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.json()
        }
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            "employee_code": employee_code,
            "error": str(e)
        }

if __name__ == "__main__":
    print("\n" + "="*80)
    print("COORDINATOR API ENDPOINT TEST")
    print("="*80)
    
    # Wait for server to be ready
    print("\nWaiting for server to be ready...")
    max_retries = 10
    for i in range(max_retries):
        try:
            requests.get(f"{BASE_URL}/", timeout=2)
            print("✓ Server is ready!")
            break
        except:
            if i < max_retries - 1:
                print(f"  Attempt {i+1}/{max_retries}: Waiting...")
                time.sleep(1)
            else:
                print("✗ Server did not respond in time")
                exit(1)
    
    # Test 1: I-code (new format)
    result1 = test_employee_search("I-2607037")
    
    # Test 2: E-code (legacy format)
    result2 = test_employee_search("E-2606026")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Test 1 (I-code): {result1.get('status_code', 'ERROR')}")
    print(f"Test 2 (E-code): {result2.get('status_code', 'ERROR')}")
    print("\n✓ All tests completed!")
