#!/usr/bin/env python3
"""Test if Render login page is accessible."""

import requests
import sys

url = "https://hr-management-system.muuzz.onrender.com/auth/login"

print(f"Testing: {url}")
print("=" * 60)

try:
    response = requests.get(url, timeout=10, allow_redirects=True)
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.content)} bytes")
    
    if response.status_code == 200:
        if "login" in response.text.lower() or "password" in response.text.lower():
            print("\n✓ SUCCESS - Login page content found!")
            print("\nThe app is WORKING. Login page is accessible.")
            sys.exit(0)
        else:
            print("\n✗ Page returned 200 but doesn't seem to be a login page")
            print(f"First 500 chars: {response.text[:500]}")
            sys.exit(1)
    elif response.status_code in [301, 302, 303, 307, 308]:
        print(f"✓ Redirect response (expected for unauthenticated users)")
        print(f"  Redirects to: {response.url if hasattr(response, 'url') else 'unknown'}")
        print("\nThe app is WORKING. Redirects are functioning.")
        sys.exit(0)
    else:
        print(f"\n✗ Unexpected status code: {response.status_code}")
        sys.exit(1)
        
except requests.exceptions.ConnectionError as e:
    print(f"\n✗ CONNECTION ERROR: {e}")
    print("App may not be running or URL is incorrect")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    sys.exit(1)
