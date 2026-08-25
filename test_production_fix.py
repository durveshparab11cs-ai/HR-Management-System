#!/usr/bin/env python
"""
Test the coordinator API endpoint to verify the production fix.
Tests both local (http://127.0.0.1:8000) and production (https://smarthrms.online)
"""

import requests
import json
import sys
from urllib.parse import urljoin

def test_endpoint(base_url, endpoint, payload, label):
    """Test a single endpoint"""
    url = urljoin(base_url, endpoint)
    
    print(f"\n{'='*70}")
    print(f"TEST: {label}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*70}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            verify=False,  # Skip SSL verification for self-signed certs
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response Body (first 500 chars): {response.text[:500]}")
        
        # Try to parse as JSON
        try:
            json_response = response.json()
            print(f"\n✓ Response is valid JSON:")
            print(json.dumps(json_response, indent=2))
            return True
        except json.JSONDecodeError as e:
            print(f"\n✗ Response is NOT valid JSON!")
            print(f"JSON Error: {e}")
            print(f"Response starts with: {response.text[:100]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False

def main():
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Test payload
    payload = {"employee_code": "E-2512012"}
    
    results = {}
    
    # Test 1: Local Flask app
    print("\n" + "="*70)
    print("PHASE 13: VERIFY PRODUCTION FIX")
    print("="*70)
    
    print("\nTEST 1: LOCAL FLASK APP (http://127.0.0.1:8000)")
    results['local'] = test_endpoint(
        'http://127.0.0.1:8000',
        '/coordinator/api/search-employee',
        payload,
        'Local API - Search Employee'
    )
    
    # Test 2: Production via Cloudflare tunnel
    print("\n\nTEST 2: PRODUCTION (https://smarthrms.online)")
    results['production'] = test_endpoint(
        'https://smarthrms.online',
        '/coordinator/api/search-employee',
        payload,
        'Production API - Search Employee'
    )
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Local API returns JSON: {'✓ PASS' if results['local'] else '✗ FAIL'}")
    print(f"Production API returns JSON: {'✓ PASS' if results['production'] else '✗ FAIL'}")
    
    if results['local'] and results['production']:
        print("\n✓ ALL TESTS PASSED - Fix is working!")
        return 0
    elif results['local']:
        print("\n⚠ Local works but production doesn't - may be tunnel/cloudflare issue")
        return 1
    else:
        print("\n✗ Local API is still broken - fix didn't work")
        return 2

if __name__ == '__main__':
    sys.exit(main())
