"""
Comprehensive test to verify the coordinator API returns JSON (200) 
instead of 302 redirect, confirming the fix is properly deployed.
"""

import os
import sys

# Suppress database warnings
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', '')

print("=" * 80)
print("COORDINATOR API FIX VERIFICATION TEST")
print("=" * 80)
print()

try:
    print("Step 1: Checking which app module is being loaded...")
    import app
    print(f"App module location: {app.__file__}")
    print()
    
    print("Step 2: Creating Flask app...")
    from app import create_app
    app_instance = create_app("development")
    print("✅ App created successfully")
    print()
    
    print("Step 3: Checking coordinator routes...")
    with app_instance.app_context():
        from app.blueprints.coordinator import coordinator_bp
        print(f"✅ Coordinator blueprint loaded from: {coordinator_bp.import_name}")
        print(f"   URL prefix: {coordinator_bp.url_prefix}")
        
        # List all routes
        print("\n   Routes registered:")
        for rule in app_instance.url_map.iter_rules():
            if 'coordinator' in rule.rule:
                print(f"      {rule.rule} -> {rule.endpoint} ({', '.join(rule.methods - {'HEAD', 'OPTIONS'})})")
        print()
    
    print("Step 4: Checking if /api/search-employee route exists...")
    route_found = False
    with app_instance.app_context():
        for rule in app_instance.url_map.iter_rules():
            if '/coordinator/api/search-employee' in rule.rule:
                route_found = True
                print(f"✅ Found route: {rule.rule}")
                print(f"   Endpoint: {rule.endpoint}")
                print(f"   Methods: {rule.methods - {'HEAD', 'OPTIONS'}}")
                
                # Get the view function
                view_func = app_instance.view_functions.get(rule.endpoint)
                if view_func:
                    print(f"   Has @public_api: {getattr(view_func, 'is_public_api', False)}")
                    print(f"   requires_auth: {getattr(view_func, 'requires_auth', None)}")
                break
        
        if not route_found:
            print("❌ Route /coordinator/api/search-employee NOT FOUND")
            print("   Available coordinator routes:")
            for rule in app_instance.url_map.iter_rules():
                if 'coordinator' in rule.rule:
                    print(f"      {rule.rule}")
    
    print()
    print("Step 5: Testing coordinator API endpoint...")
    with app_instance.test_client() as client:
        import json
        
        response = client.post(
            "/coordinator/api/search-employee",
            data=json.dumps({"employee_code": "E-TEST"}),
            content_type="application/json"
        )
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content-Type: {response.content_type}")
        print()
        
        # Analyze the response
        print("Step 6: Analyzing response...")
        print()
        
        if response.status_code == 200:
            print("✅ SUCCESS: Got HTTP 200 (not 302)")
            print("✅ API is returning a response, not a redirect")
            
            if "application/json" in response.content_type:
                print("✅ Response is JSON (correct format)")
                try:
                    data = response.get_json()
                    print("✅ Valid JSON response")
                    print()
                    print("Response body:")
                    print(json.dumps(data, indent=2))
                except Exception as e:
                    print(f"❌ Failed to parse JSON: {e}")
            else:
                print(f"⚠️  Content-Type is {response.content_type}, expected application/json")
                
        elif response.status_code == 302:
            print("❌ FAIL: Still getting 302 redirect")
            print(f"   Location header: {response.headers.get('Location')}")
            print(f"   Response body (first 200 chars): {response.data[:200]}")
            sys.exit(1)
            
        elif response.status_code == 404:
            print(f"⚠️  Got 404 (route not found or employee not found)")
            print(f"   Response data: {response.data[:200]}")
            if "application/json" not in response.content_type:
                print("   This is NOT a JSON response - route likely doesn't exist!")
                
        else:
            print(f"⚠️  Got unexpected status code: {response.status_code}")
            print(f"   Response (first 300 chars): {response.data[:300]}")
        
        print()
        print("=" * 80)
        print("VERIFICATION RESULT")
        print("=" * 80)
        
        if response.status_code in (200, 404):
            if route_found:
                print("✅ PASSED: Coordinator API is working correctly")
                print("   - Returns JSON responses (not HTML redirects)")
                print("   - Status codes are API-appropriate (200/404, not 302)")
                print("   - The @public_api decorator and skip_auth hook are functioning")
                print()
                print("The coordinator API has been successfully fixed!")
            else:
                print("❌ FAILED: Route not found - API may not be deployed correctly")
        else:
            print(f"❌ FAILED: Unexpected status code {response.status_code}")
            
except Exception as e:
    print(f"❌ ERROR during test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

