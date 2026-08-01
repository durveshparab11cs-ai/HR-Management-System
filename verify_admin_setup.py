#!/usr/bin/env python
"""
Comprehensive verification that e2606026 (Durvesh Parab) 
has super admin portal access with Admin Panel in sidebar.
"""
from app import create_app

def test_admin_setup():
    """Test that Durvesh Parab has super admin access"""
    print("=" * 70)
    print("VERIFYING DURVESH PARAB (E-2606026) SUPER ADMIN SETUP")
    print("=" * 70)
    
    app = create_app()
    
    # Test 1: User Account Exists
    print("\n[1/5] Checking user account exists...")
    with app.app_context():
        from app.models.user import User
        from app.constants.enums import UserRole
        
        user = User.query.filter_by(username='e2606026').first()
        assert user is not None, "User e2606026 not found"
        print(f"  [OK] User found: {user.full_name} (ID: {user.id})")
    
    # Test 2: Role is super_admin
    print("\n[2/5] Checking role is super_admin...")
    with app.app_context():
        user = User.query.filter_by(username='e2606026').first()
        assert user.role == 'super_admin', f"Expected role 'super_admin', got '{user.role}'"
        print(f"  [OK] Role is correctly set to: {user.role}")
    
    # Test 3: Account is active
    print("\n[3/5] Checking account is active...")
    with app.app_context():
        user = User.query.filter_by(username='e2606026').first()
        assert user.is_active == True, "User is not active"
        assert user.status == 'active', f"Status is '{user.status}', expected 'active'"
        print(f"  [OK] Account is active and not locked")
    
    # Test 4: Password verification
    print("\n[4/5] Verifying password...")
    with app.app_context():
        user = User.query.filter_by(username='e2606026').first()
        is_valid = user.check_password('TempPassword@123')
        assert is_valid, "Password 'TempPassword@123' is incorrect"
        print(f"  [OK] Password verified: TempPassword@123")
    
    # Test 5: Admin Panel in sidebar when logged in
    print("\n[5/5] Testing Admin Panel appears in sidebar when logged in...")
    with app.test_client() as client:
        # Set session to logged-in state
        with client.session_transaction() as sess:
            sess['_user_id'] = "5"  # e2606026's user ID
        
        # Request dashboard (which redirects to admin for super_admin)
        response = client.get('/dashboard/', follow_redirects=True)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert b'Admin Panel' in response.data, "Admin Panel not found in sidebar"
        print(f"  [OK] Admin Panel menu item found in sidebar")
    
    print("\n" + "=" * 70)
    print("ALL CHECKS PASSED - SUPER ADMIN SETUP VERIFIED")
    print("=" * 70)
    print("\nLogin Details:")
    print("  Employee Code: E-2606026")
    print("  Username: e2606026")
    print("  Password: TempPassword@123")
    print("  Role: super_admin")
    print("\nThe user can now access the Admin Panel from the sidebar.")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    try:
        test_admin_setup()
    except AssertionError as e:
        print(f"\n[FAIL] VERIFICATION FAILED: {e}\n")
        exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        exit(1)
