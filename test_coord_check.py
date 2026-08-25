#!/usr/bin/env python
"""Check coordinator API response format"""
import urllib.request
import json

log = open("coordinator_check.log", "w", encoding='utf-8')

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
    
    log.write("Status Code: " + str(resp.status) + "\n")
    log.write("Content-Type: " + resp.headers.get('Content-Type', 'None') + "\n")
    
    body = resp.read().decode('utf-8', errors='replace')
    log.write("Body length: " + str(len(body)) + "\n")
    log.write("First 200 chars: " + body[:200] + "\n")
    
    # Check if it's HTML
    if body.startswith('<'):
        log.write("\nRESULT: API is returning HTML (not JSON)\n")
        log.write("Response starts with: " + body[:100] + "\n")
        # Extract title if it's an HTML page
        if '<title>' in body:
            title_start = body.find('<title>') + 7
            title_end = body.find('</title>')
            title = body[title_start:title_end]
            log.write("Page title: " + title + "\n")
    elif body.startswith('{'):
        log.write("\nRESULT: API is returning JSON\n")
        try:
            data = json.loads(body)
            log.write("JSON is valid\n")
        except json.JSONDecodeError as e:
            log.write("JSON is INVALID: " + str(e) + "\n")
    else:
        log.write("\nRESULT: API response is something else\n")
        log.write("Starts with: " + repr(body[:50]) + "\n")
        
except Exception as e:
    log.write("ERROR: " + str(type(e).__name__) + ": " + str(e) + "\n")

log.close()
print("Check saved to coordinator_check.log")
