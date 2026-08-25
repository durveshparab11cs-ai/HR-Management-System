#!/usr/bin/env python3
"""
Simple test script for coordinator API endpoint
"""

import requests
import json

# Configuration
url = "http://localhost:8000/coordinator/api/search-employee"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}
payload = {
    "employee_code": "E-2606026"
}

print("=" * 70)
print("COORDINATOR API ENDPOINT TEST")
print("=" * 70)
print("\nEndpoint: " + url)
print("Payload: " + json.dumps(payload))
print("\nSending request...\n")

try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    
    # Extract information
    status_code = response.status_code
    content_type = response.headers.get('Content-Type', 'Not provided')
    response_body = response.text
    first_300_chars = response_body[:300]
    
    # Determine response type
    is_json = response_body.strip().startswith('{') or response_body.strip().startswith('[')
    is_html = '<!DOCTYPE' in response_body or '<html' in response_body.lower()
    
    response_type = "JSON" if is_json else ("HTML" if is_html else "Text/Other")
    
    # Display results
    print("RESULTS:")
    print("-" * 70)
    print("[1] HTTP Status Code: " + str(status_code))
    print("[2] Content-Type Header: " + content_type)
    print("[3] Response Type: " + response_type)
    print("[4] First 300 characters of response body:")
    print("-" * 70)
    print(first_300_chars)
    print("-" * 70)
    
    # Additional details
    print("\nAdditional Info:")
    print("  Total response length: " + str(len(response_body)) + " characters")
    
    # If JSON, try to parse and display structure
    if is_json:
        try:
            json_data = response.json()
            print("  JSON Structure: " + type(json_data).__name__)
        except json.JSONDecodeError as e:
            print("  Error parsing JSON: " + str(e))
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    
except requests.exceptions.ConnectionError as e:
    print("ERROR: Connection failed")
    print("Details: " + str(e))
    print("\nNote: Make sure the server is running on http://localhost:8000")
except requests.exceptions.Timeout:
    print("ERROR: Request timed out after 10 seconds")
except requests.exceptions.RequestException as e:
    print("ERROR: Request failed")
    print("Details: " + str(e))
except Exception as e:
    print("ERROR: Unexpected error")
    print("Details: " + type(e).__name__ + ": " + str(e))
