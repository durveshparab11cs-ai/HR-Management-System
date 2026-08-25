#!/usr/bin/env python
"""Inspect what the coordinator API is actually returning"""
import urllib.request
import json

log = open("coordinator_inspect.log", "w")

def log_write(msg):
    log.write(msg + "\n")
    log.flush()

url = "http://localhost:8000/coordinator/api/search-employee"
payload = json.dumps({"employee_code": "E-2606026"}).encode('utf-8')

try:
    req = urllib.request.Request(
        url, 
        data=payload, 
        headers={'Content-Type': 'application/json'}, 
        method='POST'
    )
    
    resp = urllib.request.urlopen(req, timeout=5)
    
    log_write("Status: " + str(resp.status))
    log_write("Content-Type: " + resp.headers.get('Content-Type', 'None'))
    
    body = resp.read().decode('utf-8')
    log_write("\n=== FULL RESPONSE BODY ===\n")
    log_write(body)
    log_write("\n=== END RESPONSE BODY ===\n")
    
    # Check if it's HTML
    if body.startswith('<'):
        log_write("\nCRITICAL: Response is HTML (starts with '<')")
        log_write("This indicates the API is redirecting or not handling JSON properly")
    
    # Try to parse as JSON
    try:
        data = json.loads(body)
        log_write("\nSUCCESS: Response parsed as JSON")
    except json.JSONDecodeError as e:
        log_write("\nERROR: Response is NOT valid JSON")
        log_write("JSON Error: " + str(e))
        
except Exception as e:
    log_write("Request failed: " + str(e))

log.close()
print("Inspection saved to coordinator_inspect.log")
