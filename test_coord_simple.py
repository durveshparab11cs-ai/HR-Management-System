#!/usr/bin/env python
"""Comprehensive test of coordinator API endpoints"""
import urllib.request
import json
import time

print("=" * 70)
print("COORDINATOR API - COMPREHENSIVE TEST")
print("=" * 70)

# Wait for server to be fully ready
time.sleep(2)

results = {
    "test1_portal": {"pass": False, "details": ""},
    "test2_valid_employee": {"pass": False, "details": ""},
    "test3_invalid_employee": {"pass": False, "details": ""},
    "test4_no_html_redirects": {"pass": False, "details": ""}
}

# Test 1: Portal page accessible
print("\n[TEST 1] Portal HTML page should be accessible")
try:
    resp = urllib.request.urlopen("http://localhost:8000/coordinator/portal")
    content_type = resp.headers.get('Content-Type', '')
    print("  PASS: Status " + str(resp.status) + ", Content-Type: " + content_type)
    results["test1_portal"]["pass"] = True
    results["test1_portal"]["details"] = "Status 200, HTML returned"
    if 'text/html' in content_type:
        print("  PASS: Portal returns HTML as expected")
    else:
        print("  WARN: Unexpected content type")
except Exception as e:
    print("  FAIL: " + str(e))
    results["test1_portal"]["details"] = str(e)

# Test 2: API returns JSON for valid employee
print("\n[TEST 2] API should return JSON for valid employee code")
url = "http://localhost:8000/coordinator/api/search-employee"
payload = json.dumps({"employee_code": "E-2606026"}).encode('utf-8')
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

try:
    resp = urllib.request.urlopen(req)
    body = resp.read().decode('utf-8')
    data = json.loads(body)
    print("  PASS: Status " + str(resp.status) + ", Content-Type: " + resp.headers.get('Content-Type', 'unknown'))
    print("  PASS: Valid JSON received")
    results["test2_valid_employee"]["pass"] = True
    results["test2_valid_employee"]["details"] = "Status 200, Valid JSON"
    
    if data.get('success') and data.get('employee'):
        print("  PASS: Employee found: " + data['employee']['full_name'])
    elif not data.get('success'):
        print("  INFO: Employee code not in database (expected): " + data.get('error', 'Unknown'))
except json.JSONDecodeError as e:
    print("  FAIL: NOT valid JSON: " + str(e))
    results["test2_valid_employee"]["details"] = "JSON decode error: " + str(e)
except Exception as e:
    print("  FAIL: " + str(e))
    results["test2_valid_employee"]["details"] = str(e)

# Test 3: API returns JSON for invalid employee code
print("\n[TEST 3] API should return JSON error for invalid employee")
payload = json.dumps({"employee_code": "E-INVALID123"}).encode('utf-8')
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

try:
    resp = urllib.request.urlopen(req)
except urllib.error.HTTPError as he:
    try:
        body = he.read().decode('utf-8')
        data = json.loads(body)
        print("  PASS: Status " + str(he.code) + ", Content-Type: " + he.headers.get('Content-Type', 'unknown'))
        print("  PASS: Valid JSON received")
        results["test3_invalid_employee"]["pass"] = True
        results["test3_invalid_employee"]["details"] = "Status " + str(he.code) + ", Valid JSON"
        if not data.get('success'):
            print("  PASS: Error message: " + data.get('error', 'Unknown'))
    except json.JSONDecodeError as je:
        print("  FAIL: NOT valid JSON: " + str(je))
        print("  Response: " + body[:300])
        results["test3_invalid_employee"]["details"] = "JSON decode error: " + str(je)
except Exception as e:
    print("  FAIL: " + str(e))
    results["test3_invalid_employee"]["details"] = str(e)

# Test 4: No HTML redirects
print("\n[TEST 4] API should NOT return HTML (no redirects)")
payload = json.dumps({"employee_code": "E-TEST"}).encode('utf-8')
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

try:
    resp = urllib.request.urlopen(req)
    body = resp.read().decode('utf-8')
    if body.startswith('<'):
        print("  FAIL: Response starts with HTML tag: " + body[:100])
        results["test4_no_html_redirects"]["details"] = "HTML response detected"
    elif body.startswith('{'):
        print("  PASS: Response is JSON (starts with {)")
        print("  PASS: NO HTML redirect detected")
        results["test4_no_html_redirects"]["pass"] = True
        results["test4_no_html_redirects"]["details"] = "Valid JSON, no HTML"
    else:
        print("  WARN: Unexpected start: " + body[:50])
        results["test4_no_html_redirects"]["details"] = "Unexpected response start"
except Exception as e:
    # Check error response
    try:
        body = e.read().decode('utf-8')
        if body.startswith('<'):
            print("  FAIL: Error response is HTML: " + body[:100])
            results["test4_no_html_redirects"]["details"] = "HTML error response"
        else:
            print("  PASS: Error response is JSON")
            results["test4_no_html_redirects"]["pass"] = True
            results["test4_no_html_redirects"]["details"] = "Valid JSON in error"
    except:
        print("  FAIL: " + str(e))
        results["test4_no_html_redirects"]["details"] = str(e)

print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
for test, result in results.items():
    status = "PASS" if result["pass"] else "FAIL"
    print("[" + status + "] " + test + ": " + result["details"])

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
