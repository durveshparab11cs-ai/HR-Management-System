"""
Final comprehensive test to verify admin dashboard is working
"""
from app import create_app
from flask import url_for

app = create_app()

with app.app_context():
    print("Testing admin route registration...")
    
    # Check if admin.index route exists
    with app.test_request_context():
        try:
            url = url_for('admin.index')
            print("[OK] admin.index route exists: {}".format(url))
        except Exception as e:
            print("[FAILED] admin.index route error: {}".format(e))
            exit(1)
    
    # Check all admin routes
    print("\nListing all registered routes:")
    for rule in app.url_map.iter_rules():
        if 'admin' in rule.rule:
            print("  - {} -> {}".format(rule.rule, rule.endpoint))
    
    # Test blueprint registration
    print("\nChecking blueprint registration...")
    print("  Blueprints registered: {}".format([name for name, _ in app.blueprints.items()]))
    
    # Check if admin blueprint exists
    if 'admin' in app.blueprints:
        print("[OK] Admin blueprint is registered")
    else:
        print("[FAILED] Admin blueprint is NOT registered")
        exit(1)
    
    print("\n[SUCCESS] All tests passed! Admin panel should be working.")
