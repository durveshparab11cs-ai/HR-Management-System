# Quick Fix: Super Admin Roles Not Updated

## If E-2512012 or E-2603025 still don't have super_admin role

### ⏱️ 2-Minute Fix via Render One-Off Dyno

1. **Go to Render Dashboard**
   - https://dashboard.render.com

2. **Find your app:** "hr-management-system-muqz"

3. **Click "Resources" tab**

4. **Click "New One-Off Dyno"**

5. **Paste this command and press Enter:**
   ```
   python smart_hrms/manual_fix_admin_roles.py
   ```

6. **Watch for ✅ confirmations:**
   ```
   ✅ ALL CHANGES COMMITTED SUCCESSFULLY
   ✅ E-2512012: role=super_admin
   ✅ E-2603025: role=super_admin
   ```

7. **Done!** Users now have super_admin role

---

## If still doesn't work:

### Check Logs
```
Dashboard → Logs → Search: "ENSURE_ADMIN"
```
Look for these lines:
- ✅ "ENSURE_ADMIN: ▶ Starting admin role verification"
- ✅ "ENSURE_ADMIN: Checking employee code E-2512012"
- ✅ "ENSURE_ADMIN: Routine completed successfully"

If you see ❌ errors, note them and send to support.

---

## Local Test (Before Render)

```bash
cd "c:\Users\durve\Downloads\HR management system"
python smart_hrms/manual_fix_admin_roles.py
```

Should output:
```
✅ ALL CHANGES COMMITTED SUCCESSFULLY
✅ E-2512012...role=super_admin
✅ E-2603025...role=super_admin
FIX COMPLETE
```

---

## Verify It Worked

1. **Go to app:** https://hr-management-system-muqz.onrender.com
2. **Login as:** e_2512012 or e_2603025
3. **You should see:** Admin dashboard (not employee dashboard)
4. **Check role:**
   - Look for admin menu in sidebar
   - Should have access to admin panel

---

## Database Query (Advanced)

Connect to Render PostgreSQL and run:

```sql
SELECT username, role FROM users WHERE username IN ('e2512012', 'e2603025') ORDER BY username;
```

Should show:
```
   username  |    role
   -----------+-----------
   e2512012   | super_admin
   e2603025   | super_admin
```

---

## Last Resort: Manual Database Update

If script still fails, manually set role in database:

```sql
UPDATE users SET role = 'super_admin' 
WHERE username IN ('e2512012', 'e2603025');
```

Then verify:
```sql
SELECT username, role FROM users WHERE username IN ('e2512012', 'e2603025');
```

---

## Contact Support If:
- ❌ Script fails with database error
- ❌ Roles still not updating after manual script
- ❌ "Employee code not found" error
- ❌ Can't connect to Render PostgreSQL

Send them:
1. Full error message from script output
2. Results of: `SELECT COUNT(*) FROM employee WHERE employee_code IN ('E-2512012', 'E-2603025');`
3. Render logs (search "ENSURE_ADMIN")
