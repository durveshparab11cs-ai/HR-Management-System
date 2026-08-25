#!/usr/bin/env python
"""Test coordinator API with debugging"""
import urllib.request
import json
import time

log = open("coordinator_debug.log", "w")

def log_write(msg):
    print(msg)
    log.write(msg + "\n")
    log.flush()

log_write("=" * 70)
log_write("COORDINATOR API - DEBUG TEST")
log_write("=" * 70)

# Test the API directly
log_write("\n[TEST] Simple API call to /coordinator/api/search-employee")
url = "http://localhost:8000/coordinator/api/search-employee"
payload = json.dumps({"employee_code": "E-2606026"}).encode('utf-8')

log_write("URL: " + url)
log_write("Payload: E-2606026")
log_write("Timeout: 5 seconds")

try:
    log_write("Creating request...")
    req = urllib.request.Request(
        url, 
        data=payload, 
        headers={'Content-Type': 'application/json'}, 
        method='POST'
    )
    
    log_write("Opening URL with 5 second timeout...")
    start = time.time()
    resp = urllib.request.urlopen(req, timeout=5)
    elapsed = time.time() - start
    
    log_write("Got response after " + str(round(elapsed, 2)) + " seconds")
    log_write("Status: " + str(resp.status))
    log_write("Content-Type: " + resp.headers.get('Content-Type', 'None'))
    
    log_write("Reading body...")
    body = resp.read().decode('utf-8')
    log_write("Body length: " + str(len(body)))
    
    log_write("Parsing JSON...")
    data = json.loads(body)
    log_write("SUCCESS: Got valid JSON")
    log_write("JSON: " + json.dumps(data, indent=2)[:500])
    
except urllib.error.HTTPError as he:
    log_write("Got HTTP Error: " + str(he.code))
    try:
        body = he.read().decode('utf-8')
        log_write("Error body length: " + str(len(body)))
        log_write("Error body starts with: " + body[:100])
        try:
            data = json.loads(body)
            log_write("Error is valid JSON")
        except:
            log_write("Error is NOT valid JSON")
    except:
        log_write("Could not read error body")
        
except socket.timeout:
    log_write("TIMEOUT: Request took too long")
except Exception as e:
    log_write("ERROR: " + str(type(e).__name__) + ": " + str(e))

log_write("\n" + "=" * 70)
log_write("TEST COMPLETE")
log_write("=" * 70)

log.close()
print("Debug log saved to coordinator_debug.log")
