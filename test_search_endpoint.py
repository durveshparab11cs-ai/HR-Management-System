"""
Test the coordinator search endpoint directly without browser.
This helps isolate whether the issue is backend or frontend.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

print("\n" + "="*70)
print("COORDINATOR SEARCH ENDPOINT TEST")
print("="*70 + "\n")

# Test 1: Search by exact employee code
print("Test 1: Search by exact employee code E-2606026")
print("-" * 70)

try:
    response = requests.post(
        f"{BASE_URL}/coordinator/search",
        json={"search_term": "E-2606026"},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(json.dumps(response.json(), indent=2))
    
    data = response.json()
    if data.get("success"):
        emp = data.get("employee")
        print(f"\n✅ SUCCESS: Found {emp.get('full_name')} ({emp.get('employee_code')})")
    else:
        print(f"\n❌ FAILED: {data.get('error')}")
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Cannot connect to server. Is it running on localhost:5000?")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

print("\n" + "-" * 70 + "\n")

# Test 2: Search by partial code
print("Test 2: Search by partial employee code E-2606")
print("-" * 70)

try:
    response = requests.post(
        f"{BASE_URL}/coordinator/search",
        json={"search_term": "E-2606"},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    
    if data.get("success"):
        emp = data.get("employee")
        print(f"✅ Found: {emp.get('full_name')} ({emp.get('employee_code')})")
    else:
        print(f"❌ Not found: {data.get('error')}")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

print("\n" + "-" * 70 + "\n")

# Test 3: Search by name
print("Test 3: Search by name 'Durvesh'")
print("-" * 70)

try:
    response = requests.post(
        f"{BASE_URL}/coordinator/search",
        json={"search_term": "Durvesh"},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    
    if data.get("success"):
        emp = data.get("employee")
        print(f"✅ Found: {emp.get('full_name')} ({emp.get('employee_code')})")
    else:
        print(f"❌ Not found: {data.get('error')}")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70 + "\n")

print("IMPORTANT NOTES:")
print("- This test BYPASSES authentication (no @login_required check)")
print("- Real browser requests MUST be authenticated via coordinator login")
print("- If this test passes, the issue is likely in frontend JavaScript")
print("- If this test fails, the issue is in backend search logic")
print("\n")
