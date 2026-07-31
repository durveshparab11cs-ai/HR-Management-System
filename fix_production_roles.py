#!/usr/bin/env python
"""
Direct fix for production database - Update user roles to super_admin
This script connects directly to the Render PostgreSQL database and updates roles
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse

# Production database credentials
DB_URL = "postgresql://smart_hrms_user:Wis56fwoyP8EKmR8GYSFGGXBinU3Hp2G@dpg-d9bl4t7aqgkc739jhup0-a/smart_hrms"

# Parse connection string
parsed = urllib.parse.urlparse(DB_URL)

print("=" * 70)
print("FIXING PRODUCTION DATABASE ROLES")
print("=" * 70)
print()

try:
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("✅ Connected to production database!")
    print()
    
    # Step 1: Check current state
    print("1️⃣  CHECKING CURRENT STATE...")
    cursor.execute("""
        SELECT id, username, email, role 
        FROM users 
        WHERE username IN ('e_2512012', 'e_2603025')
        ORDER BY username
    """)
    
    current_users = cursor.fetchall()
    print(f"\n   Found {len(current_users)} users:")
    
    if len(current_users) == 0:
        print("   ❌ NO USERS FOUND WITH THESE USERNAMES")
        print()
        print("   First 20 users in database:")
        cursor.execute("SELECT id, username, email, role FROM users ORDER BY id LIMIT 20")
        all_users = cursor.fetchall()
        for user in all_users:
            print(f"   - ID {user['id']}: {user['username']}: {user['role']} ({user['email']})")
    else:
        for user in current_users:
            status = "✅" if user['role'] == 'super_admin' else "❌"
            print(f"   {status} {user['username']}: {user['role']} ({user['email']})")
    
    print()
    
    # Step 2: Update roles
    if len(current_users) > 0:
        print("2️⃣  UPDATING ROLES TO 'super_admin'...")
        cursor.execute("""
            UPDATE users 
            SET role = 'super_admin'
            WHERE username IN ('e_2512012', 'e_2603025')
        """)
        
        conn.commit()
        print(f"   ✅ Updated {cursor.rowcount} user(s)")
        print()
        
        # Step 3: Verify
        print("3️⃣  VERIFYING CHANGES...")
        cursor.execute("""
            SELECT id, username, email, role 
            FROM users 
            WHERE username IN ('e_2512012', 'e_2603025')
            ORDER BY username
        """)
        
        verified_users = cursor.fetchall()
        for user in verified_users:
            status = "✅" if user['role'] == 'super_admin' else "❌"
            print(f"   {status} {user['username']}: {user['role']}")
        
        print()
        print("=" * 70)
        print("✅ PRODUCTION DATABASE UPDATED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print("👉 Both users should now see the admin dashboard")
        print("👉 Refresh the website or clear your browser cache")
        print()
    else:
        print("❌ Cannot update - users not found in database")
    
    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
