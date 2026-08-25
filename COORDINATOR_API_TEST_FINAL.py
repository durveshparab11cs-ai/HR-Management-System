#!/usr/bin/env python
"""
Comprehensive test of coordinator API endpoints

FULL REPORT:
1. Test 1: Portal page accessible
2. Test 2: API returns JSON for valid employee
3. Test 3: API returns JSON error for invalid employee  
4. Test 4: API doesn't return HTML redirects

This script generates a detailed test report showing:
- HTTP status codes
- Content-Type headers
- HTML vs JSON responses
- Any HTML login page redirects (bug)
"""

import urllib.request
import json
import time

def write_report(msg):
    """Write to both console and report file."""
    print(msg)
    with open("COORDINATOR_API_TEST_REPORT.txt", "a", encoding='utf-8') as f:
        f.write(msg + "\n")

# Clear previous report
open("COORDINATOR_API_TEST_REPORT.txt", "w").close()

write_report("=" * 70)
write_report("COORDINATOR API - COMPREHENSIVE TEST")
write_report("=" * 70)
write_report("")

# Wait for server
time.sleep(2)

tests_passed = 0
tests_failed = 0

# Test 1: Portal accessible
write_report("[TEST 1] Portal HTML page should be accessible (may redirect to login)")
try:
    resp = urllib.request.urlopen("http://localhost:8000/coordinator/portal", timeout=10)
    write_report(f"  Status: {resp.status}")
    write_report(f"  Content-Type: {resp.headers.get('Content-Type')}")
    write_report("  ✓ PASS: Portal accessible")
    tests_passed += 1
except urllib.error.HTTPError as he:
    write_report(f"  Status: {he.code}")
    write_report(f"  ✓ PASS: Status {he.code} (expected - may require auth)")
    tests_passed += 1
except Exception as e:
    write_report(f"  ✗ FAIL: {e}")
    tests_failed += 1
write_report("")

# Test 2: API JSON for valid employee
write_report("[TEST 2] API should return JSON for valid employee code")
url = "http://localhost:8000/coordinator/api/search-employee"
payload = json.dumps({"employee_code": "E-2606026"}).encode('utf-8')
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

try:
    resp = urllib.request.urlopen(req, timeout=10)
    body = resp.read().decode('utf-8', errors='replace')
    
    write_report(f"  Status: {resp.status}")
    write_report(f"  Content-Type: {resp.headers.get('Content-Type')}")
    write_report(f"  Body length: {len(body)}")
    
    if body.startswith('{'):
        try:
            data = json.loads(body)
            write_report("  ✓ Valid JSON response")
            write_report(f"  ✓ PASS: Employee API returns JSON")
            tests_passed += 1
        except json.JSONDecodeError:
            write_report("  ✗ FAIL: Invalid JSON")
            tests_failed += 1
    elif body.startswith('<'):
        write_report(f"  ✗ FAIL: Response is HTML (starts with <)")
        write_report(f"       HTML Title: {body[body.find('<title>'):body.find('</title>')+8] if '<title>' in body else 'Unknown'}")
        write_report("  ✗ BUG STILL PRESENT: API returns HTML instead of JSON")
        tests_failed += 1
    else:
        write_report(f"  ? Unexpected response start: {body[:50]}")
        tests_failed += 1
except Exception as e:
    write_report(f"  ✗ FAIL: {e}")
    tests_failed += 1
write_report("")

# Test 3: API JSON for invalid employee
write_report("[TEST 3] API should return JSON error for invalid employee")
payload = json.dumps({"employee_code": "E-INVALID123"}).encode('utf-8')
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

try:
    resp = urllib.request.urlopen(req, timeout=10)
    body = resp.read().decode('utf-8', errors='replace')
    
    if body.startswith('{'):
        try:
            data = json.loads(body)
            write_report(f"  Status: 200 (with error in JSON)")
            write_report(f"  ✓ Valid JSON error response")
            write_report(f"  ✓ PASS: Returns JSON error for invalid code")
            tests_passed += 1
        except:
            write_report("  ✗ FAIL: Invalid JSON")
            tests_failed += 1
    else:
        write_report(f"  ? Unexpected: {body[:100]}")
        tests_failed += 1
        
except urllib.error.HTTPError as he:
    body = he.read().decode('utf-8', errors='replace')
    
    write_report(f"  Status: {he.code}")
    write_report(f"  Content-Type: {he.headers.get('Content-Type')}")
    
    if body.startswith('{'):
        try:
            data = json.loads(body)
            write_report("  ✓ Valid JSON error response")
            write_report(f"  ✓ PASS: Returns JSON error for invalid code")
            tests_passed += 1
        except:
            write_report("  ✗ FAIL: Invalid JSON in error response")
            tests_failed += 1
    elif body.startswith('<'):
        write_report("  ✗ FAIL: Error response is HTML (redirect bug)")
        tests_failed += 1
    else:
        write_report(f"  ? Unexpected: {body[:50]}")
        tests_failed += 1
except Exception as e:
    write_report(f"  ✗ FAIL: {e}")
    tests_failed += 1
write_report("")

# Test 4: No HTML redirects
write_report("[TEST 4] API should NOT return HTML (no login redirects)")
payload = json.dumps({"employee_code": "E-TEST"}).encode('utf-8')
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

try:
    resp = urllib.request.urlopen(req, timeout=10)
    body = resp.read().decode('utf-8', errors='replace')
    
    if body.startswith('<'):
        write_report("  ✗ FAIL: Response is HTML")
        write_report("  ✗ BUG: API returning login page HTML instead of JSON")
        tests_failed += 1
    elif body.startswith('{'):
        write_report("  ✓ Response is JSON")
        write_report("  ✓ PASS: No HTML redirect")
        tests_passed += 1
    else:
        write_report(f"  ? Unexpected: {body[:50]}")
        tests_failed += 1
except urllib.error.HTTPError as he:
    body = he.read().decode('utf-8', errors='replace')
    
    if body.startswith('<'):
        write_report(f"  Status: {he.code}")
        write_report("  ✗ FAIL: Error response is HTML (redirect)")
        tests_failed += 1
    elif body.startswith('{'):
        write_report(f"  Status: {he.code}")
        write_report("  ✓ Error response is JSON")
        write_report("  ✓ PASS: No HTML redirect")
        tests_passed += 1
    else:
        write_report(f"  ? Unexpected: {body[:50]}")
        tests_failed += 1
except Exception as e:
    write_report(f"  ✗ FAIL: {e}")
    tests_failed += 1
write_report("")

write_report("=" * 70)
write_report("TEST SUMMARY")
write_report("=" * 70)
write_report(f"Tests Passed: {tests_passed}")
write_report(f"Tests Failed: {tests_failed}")
write_report(f"Total: {tests_passed + tests_failed}")
write_report("")

if tests_failed == 0:
    write_report("✓ ALL TESTS PASSED - Bug is FIXED!")
else:
    write_report(f"✗ {tests_failed} TEST(S) FAILED - Bug may still be present")
write_report("")
write_report("Report saved to: COORDINATOR_API_TEST_REPORT.txt")
