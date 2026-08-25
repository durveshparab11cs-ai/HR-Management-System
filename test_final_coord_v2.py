#!/usr/bin/env python
"""Comprehensive test of coordinator API endpoints"""
import urllib.request
import json
import time
import socket

# Open log file for writing
log = open("coordinator_final_test_v2.log", "w")

def log_write(msg):
    print(msg)
    log.write(msg + "\n")
    log.flush()

log_write("=" * 70)
log_write("COORDINATOR API - COMPREHENSIVE TEST V2")
log_write("=" * 70)

# First check if server is alive
log_write("\n[CONNECTIVITY] Testing server connectivity...")
try:
    sock = socket.create_connection(("localhost", 8000), timeout=5)
    sock.close()
    log_write("  PASS: Server is responding on port 8000")
except socket.timeout:
    log_write("  FAIL: Server timeout on port 8000")
except Exception as e:
    log_write("  FAIL: Connection error: " + str(e))

results = {
    "test1_portal": {"pass": False, "details": ""},
    "test2_api_valid_json": {"pass": False, "details": ""},
    "test3_api_invalid_json": {"pass": False, "details": ""},
    "test4_no_html_redirects": {"pass": False, "details": ""}
}

# Test 1: Try to access portal (might redirect to login)
log_write("\n[TEST 1] Portal page should be accessible (may redirect to login)")
try:
    req = urllib.request.Request("http://localhost:8000/coordinator/portal")
    req.add_header('User-Agent', 'Mozilla/5.0')
    resp = urllib.request.urlopen(req, timeout=10)
    content_type = resp.headers.get('Content-Type', '')
    log_write("  PASS: Status " + str(resp.status) + ", Content-Type: " + content_type)
    results["test1_portal"]["pass"] = True
    results["test1_portal"]["details"] = "Status " + str(resp.status) + ", HTML returned"
except urllib.error.HTTPError as he:
    # 302 redirect is acceptable
    content_type = he.headers.get('Content-Type', '')
    log_write("  INFO: Status " + str(he.code) + " (redirect/auth wall), Content-Type: " + content_type)
    results["test1_portal"]["pass"] = True
    results["test1_portal"]["details"] = "Status " + str(he.code) + " (expected - auth wall)"
except Exception as e:
    log_write("  FAIL: " + str(e))
    results["test1_portal"]["details"] = str(e)

# Test 2: API returns JSON for valid employee
log_write("\n[TEST 2] API should return JSON for valid employee code")
url = "http://localhost:8000/coordinator/api/search-employee"
payload = json.dumps({"employee_code": "E-2606026"}).encode('utf-8')
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

try:
    resp = urllib.request.urlopen(req, timeout=10)
    body = resp.read().decode('utf-8')
    data = json.loads(body)
    log_write("  PASS: Status " + str(resp.status) + ", Content-Type: " + resp.headers.get('Content-Type', 'unknown'))
    log_write("  PASS: Valid JSON received")
    results["test2_api_valid_json"]["pass"] = True
    results["test2_api_valid_json"]["details"] = "Status " + str(resp.status) + ", Valid JSON"
    
    if data.get('success') and data.get('employee'):
        log_write("  PASS: Employee found: " + str(data['employee'].get('full_name', 'Unknown')))
    elif not data.get('success'):
        log_write("  INFO: Employee code not in database: " + str(data.get('error', 'Unknown')))
except json.JSONDecodeError as e:
    log_write("  FAIL: NOT valid JSON: " + str(e))
    results["test2_api_valid_json"]["details"] = "JSON decode error"
except Exception as e:
    log_write("  FAIL: " + str(e))
    results["test2_api_valid_json"]["details"] = str(e)

# Test 3: API returns JSON for invalid employee code
log_write("\n[TEST 3] API should return JSON error for invalid employee")
payload = json.dumps({"employee_code": "E-INVALID123"}).encode('utf-8')
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

try:
    resp = urllib.request.urlopen(req, timeout=10)
    body = resp.read().decode('utf-8')
    # If we get 200 with error in JSON, that's still valid
    try:
        data = json.loads(body)
        log_write("  PASS: Status " + str(resp.status) + ", Valid JSON (error response)")
        results["test3_api_invalid_json"]["pass"] = True
        results["test3_api_invalid_json"]["details"] = "Status 200, Valid JSON with error"
    except json.JSONDecodeError:
        log_write("  FAIL: NOT valid JSON in 200 response")
        results["test3_api_invalid_json"]["details"] = "Invalid JSON in success response"
except urllib.error.HTTPError as he:
    try:
        body = he.read().decode('utf-8')
        data = json.loads(body)
        log_write("  PASS: Status " + str(he.code) + ", Valid JSON error response")
        results["test3_api_invalid_json"]["pass"] = True
        results["test3_api_invalid_json"]["details"] = "Status " + str(he.code) + ", Valid JSON"
    except json.JSONDecodeError as je:
        log_write("  FAIL: NOT valid JSON in error response: " + str(je))
        log_write("  Response preview: " + body[:200])
        results["test3_api_invalid_json"]["details"] = "Invalid JSON in error response"
except Exception as e:
    log_write("  FAIL: " + str(e))
    results["test3_api_invalid_json"]["details"] = str(e)

# Test 4: No HTML redirects in API
log_write("\n[TEST 4] API should NOT return HTML (no redirects)")
payload = json.dumps({"employee_code": "E-TEST"}).encode('utf-8')
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

try:
    resp = urllib.request.urlopen(req, timeout=10)
    body = resp.read().decode('utf-8')
    if body.startswith('<'):
        log_write("  FAIL: Response starts with HTML tag: " + body[:100])
        results["test4_no_html_redirects"]["details"] = "HTML response (redirect bug)"
    elif body.startswith('{'):
        log_write("  PASS: Response is JSON (starts with {)")
        results["test4_no_html_redirects"]["pass"] = True
        results["test4_no_html_redirects"]["details"] = "Valid JSON, no HTML"
    else:
        log_write("  WARN: Unexpected response start: " + body[:50])
        results["test4_no_html_redirects"]["details"] = "Unexpected response start"
except urllib.error.HTTPError as he:
    try:
        body = he.read().decode('utf-8')
        if body.startswith('<'):
            log_write("  FAIL: Error response is HTML: " + body[:150])
            results["test4_no_html_redirects"]["details"] = "HTML error response (redirect bug)"
        elif body.startswith('{'):
            log_write("  PASS: Error response is JSON")
            results["test4_no_html_redirects"]["pass"] = True
            results["test4_no_html_redirects"]["details"] = "Valid JSON error response"
        else:
            log_write("  FAIL: Unexpected error response start")
            results["test4_no_html_redirects"]["details"] = "Unexpected error response"
    except Exception as parse_err:
        log_write("  FAIL: Could not parse error response: " + str(parse_err))
        results["test4_no_html_redirects"]["details"] = "Parse error on error response"
except Exception as e:
    log_write("  FAIL: " + str(e))
    results["test4_no_html_redirects"]["details"] = str(e)

log_write("\n" + "=" * 70)
log_write("FINAL SUMMARY")
log_write("=" * 70)
pass_count = 0
fail_count = 0
for test, result in results.items():
    status = "PASS" if result["pass"] else "FAIL"
    if result["pass"]:
        pass_count += 1
    else:
        fail_count += 1
    log_write("[" + status + "] " + test)
    log_write("    " + result["details"])

log_write("\n" + "=" * 70)
log_write("RESULTS: " + str(pass_count) + " PASSED, " + str(fail_count) + " FAILED")
log_write("=" * 70)

log.close()
print("Test results saved to coordinator_final_test_v2.log")
