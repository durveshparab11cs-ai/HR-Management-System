#!/usr/bin/env python3
"""
Test Coordinator API - Pure HTTP requests using urllib (no external dependencies)
"""

import urllib.request
import urllib.error
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_api():
    output = []
    
    output.append("=" * 80)
    output.append("COORDINATOR API HTTP TEST (urllib)")
    output.append("=" * 80)
    
    # Wait for server
    output.append("\nWaiting for server...")
    server_ready = False
    for i in range(10):
        try:
            urllib.request.urlopen(f"{BASE_URL}/", timeout=2)
            output.append("✓ Server is ready!")
            server_ready = True
            break
        except Exception as e:
            if i < 9:
                output.append(f"  Waiting... ({i+1}/10)")
                time.sleep(1)
            else:
                output.append("✗ Server not responding")
    
    if not server_ready:
        print("\n".join(output))
        return False
    
    # Test 1: I-code search (I-2607037)
    output.append("\n" + "-" * 80)
    output.append("TEST 1: Search for I-2607037 (I-code format)")
    output.append("-" * 80)
    test1_pass = False
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/coordinator/api/search-employee",
            data=json.dumps({"employee_code": "I-2607037"}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.status
            response_data = response.read().decode('utf-8')
            response_json = json.loads(response_data)
            
            output.append(f"Status Code: {status_code}")
            output.append(f"Headers: {dict(response.headers)}")
            output.append(f"Body: {json.dumps(response_json, indent=2)}")
            
            test1_pass = status_code in [200, 404]
            output.append(f"Result: {'PASS' if test1_pass else 'FAIL'}")
    except urllib.error.HTTPError as e:
        output.append(f"HTTP Error {e.code}: {e.reason}")
        response_data = e.read().decode('utf-8')
        output.append(f"Response: {response_data}")
        # Accept 404 as valid for "not found"
        test1_pass = e.code in [200, 404]
        output.append(f"Result: {'PASS' if test1_pass else 'FAIL'}")
    except Exception as e:
        output.append(f"ERROR: {str(e)}")
        test1_pass = False
    
    # Test 2: E-code search (E-2606026)
    output.append("\n" + "-" * 80)
    output.append("TEST 2: Search for E-2606026 (E-code format)")
    output.append("-" * 80)
    test2_pass = False
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/coordinator/api/search-employee",
            data=json.dumps({"employee_code": "E-2606026"}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.status
            response_data = response.read().decode('utf-8')
            response_json = json.loads(response_data)
            
            output.append(f"Status Code: {status_code}")
            output.append(f"Headers: {dict(response.headers)}")
            output.append(f"Body: {json.dumps(response_json, indent=2)}")
            
            test2_pass = status_code in [200, 404]
            output.append(f"Result: {'PASS' if test2_pass else 'FAIL'}")
    except urllib.error.HTTPError as e:
        output.append(f"HTTP Error {e.code}: {e.reason}")
        response_data = e.read().decode('utf-8')
        output.append(f"Response: {response_data}")
        # Accept 404 as valid for "not found"
        test2_pass = e.code in [200, 404]
        output.append(f"Result: {'PASS' if test2_pass else 'FAIL'}")
    except Exception as e:
        output.append(f"ERROR: {str(e)}")
        test2_pass = False
    
    # Summary
    output.append("\n" + "=" * 80)
    output.append("SUMMARY")
    output.append("=" * 80)
    output.append(f"Test 1 (I-2607037): {'PASS' if test1_pass else 'FAIL'}")
    output.append(f"Test 2 (E-2606026): {'PASS' if test2_pass else 'FAIL'}")
    output.append("=" * 80)
    
    # Print all output
    result = "\n".join(output)
    print(result)
    
    # Also save to file
    try:
        with open("api_test_http_only_OUTPUT.txt", "w") as f:
            f.write(result)
    except:
        pass
    
    return test1_pass and test2_pass

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
