# Quick Start: Coordinator Portal

## URLs to Access

| Role | URL | Purpose |
|------|-----|---------|
| **Coordinator / HR Staff** | `https://192.168.0.205:8000/coordinator/` | Mark attendance, search employees |
| **Employee (any)** | `https://192.168.0.205:8000/coordinator/employee` | View attendance, apply leave |
| **Super Admin** | `https://192.168.0.205:8000/admin/` | System monitoring & settings |

---

## 1. For HR Coordinators

### How to Mark Attendance

```
1. Open https://192.168.0.205:8000/coordinator/
2. Log in with your employee code + password (e.g., E-2512012)
3. Select your work center/location
4. In the "Search Employee" box, type:
   - Employee code (E-2603028)
   - Name (John or Doe)
   - Department (Sales)
5. Click on employee from search results
6. Click "Mark Check-In" to check them in
7. Click "Mark Check-Out" to check them out
8. Attendance recorded ✅
```

### Key Features
- **Real-time search**: Type 2+ characters, get instant results
- **Today's summary**: See checked-in, checked-out, absent count
- **No GPS needed**: Uses office location coordinates (no mobile app required)
- **Instant confirmation**: Message shows check-in/out time

### Tips
- Use employee code for faster search (e.g., E-260)
- Filter by location if managing multiple centers
- Refresh page to see updated summary

---

## 2. For Employees

### How to View Attendance & Apply Leave

```
1. Open https://192.168.0.205:8000/coordinator/employee
2. Click "My Attendance" to view check-in/out history
3. Click "Apply Leave" to request time off
4. Click "Half Day" for half-day leave
5. Click "Calendar" to see all your leaves & holidays
```

### What You Can Do
- View daily attendance (check-in/out times)
- View working hours
- Apply for vacation/sick/half-day leave
- Request shift changes
- Check approved leaves in calendar
- See leave balance

### Important
- **You don't need to do anything for check-in/check-out**
  - Your coordinator marks you in/out on the center PC
  - You can only view it, not mark yourself
- **To apply leave**: Log in with your employee code + password

---

## 3. For Super Admins

### Dashboard Access
```
https://192.168.0.205:8000/admin/
```

### What You Can See
- ✅ All attendance across all centers
- ✅ Late arrivals report
- ✅ Absent employees
- ✅ Daily attendance summary
- ✅ Reports & exports
- ✅ System settings
- ✅ User management

### Key Tasks
1. **Configure Locations**: Add office addresses & GPS coordinates
2. **Assign Employees**: Assign employees to their work centers
3. **View Reports**: Generate daily/weekly/monthly reports
4. **Manage Users**: Create coordinators, set roles & permissions

---

## 4. Common Tasks

### Task 1: Mark Attendance for 50 Employees
```
Time: ~5 minutes
Steps:
1. Open coordinator dashboard
2. For each employee:
   - Search by code (instant)
   - Click Mark Check-In
   - Next employee
3. Summary auto-updates
```

### Task 2: Find Late Arrivals
```
1. Open coordinator dashboard
2. Check "Late" count in Today's Summary
3. Click on late employees to see late minutes
4. Can export report from Admin
```

### Task 3: Employee Forgot to Mark Leave
```
1. Go to Admin → Leave Management
2. Find employee
3. Create leave record manually
4. Set approval status
5. Employee sees it in calendar
```

### Task 4: Transfer Employee to Another Center
```
1. Go to Admin → Employees
2. Find employee
3. Edit → Change "Office Location"
4. Save
5. Coordinator at new location can now mark them
```

---

## 5. Attendance Status

Employees can have these statuses:

| Status | Meaning | Who Marks |
|--------|---------|-----------|
| **Present** | Checked in & out | Coordinator |
| **Absent** | No check-in | Admin (manual) |
| **Half Day** | Checked in but left early | Coordinator or Employee request |
| **On Leave** | Approved leave | Employee request + Manager approval |
| **Holiday** | Company holiday | Admin (pre-configured) |
| **Weekend** | Saturday/Sunday | Automatic |
| **Work From Home** | Remote work | Admin or Employee |

---

## 6. Reports & Exports

### What Reports Are Available
- Daily attendance report (all employees)
- Weekly trends (check-in times, working hours)
- Monthly absence patterns
- Late arrivals (with reasons)
- Leave utilization (by type)
- Overtime report (by employee)

### How to Generate
1. Go to Admin Dashboard
2. Click "Reports"
3. Select date range & filters
4. Click "Generate" or "Export to Excel"

---

## 7. Troubleshooting

### Problem: Employee Not Found in Search
**Solution:**
- Check employee code spelling (e.g., E-2603028)
- Try searching by name instead
- Verify employee is not on leave/inactive
- Ensure employee is assigned to your location

### Problem: "Office Not Configured"
**Solution:**
- Go to Admin → Office Locations
- Add your work center with:
  - Center name
  - Address
  - GPS coordinates
- Assign employees to this center

### Problem: Time Shows Incorrectly
**Solution:**
- Times are stored in UTC, displayed in IST (India Standard Time)
- If shows wrong: check server timezone
- Browser shows local converted time (correct)

### Problem: Can't Access Coordinator Portal
**Solution:**
- Check you have HR Staff role or above
- Log out and log in again
- Clear browser cache (Ctrl+Shift+Delete)
- Check internet connection to 192.168.0.205:8000

### Problem: Check-In Says "Already Checked In"
**Solution:**
- Employee already checked in today
- Check "Today's Summary" to verify
- To correct: Admin → Regularization → Edit attendance

---

## 8. Database Integrity

### Manual Attendance Edit (Admin Only)
If attendance record is wrong:

1. Go to Admin → Attendance Management
2. Find the date & employee
3. Click "Edit"
4. Correct check-in/out times
5. Add regularization reason (audit trail)
6. Save

### Bulk Operations (Admin Only)
- Mark all absent (for holidays)
- Adjust working hours
- Apply leave to multiple employees
- Export to Excel/CSV

---

## 9. Security

### Access Control
- **Public**: Employee portal (no login)
- **HR Staff+**: Coordinator portal (login required)
- **Admin+**: Admin dashboard (login required)

### What's Protected
- Employee data: Only visible to coordinators/admin
- Attendance records: Audit logged
- Salary data: Only HR can access
- System settings: Only super admin

### Best Practices
- Don't share login credentials
- Log out when stepping away
- Use strong passwords (12+ characters)
- Change password every 90 days

---

## 10. Performance & Scalability

### Can Handle
- ✅ 1000+ employees
- ✅ 100+ simultaneous users
- ✅ 10+ work centers
- ✅ Real-time search & updates
- ✅ Multi-year attendance history

### Optimization Tips
- Use employee code search (faster than name)
- Filter by location to reduce results
- Close unused browser tabs
- Update browser to latest version

---

## 11. Mobile Access

### Can You Use Mobile?
- **Coordinator Portal**: Yes (responsive design)
  - Search, mark attendance from phone
  - View today's summary
  - All features work on mobile

- **Employee Portal**: Yes (fully responsive)
  - View attendance on phone
  - Apply leave from mobile
  - Check calendar anytime

### Requirements
- HTTPS access (https://192.168.0.205:8000)
- On company network or VPN
- Chrome/Safari/Firefox browser

---

## 12. Contact & Support

### For Technical Issues
Contact IT Team:
- Email: it@company.com
- Phone: +91-XXXX-XXXX
- Internal: IT@Corp

### For Attendance Questions
Contact HR Coordinator:
- Email: hr@company.com
- Desk: HR Office, 2nd Floor
- Internal: HR@Corp

### For Feature Requests
Contact Product Team:
- Email: product@company.com
- System: Feedback form in app

---

**Last Updated:** August 14, 2026  
**Version:** 1.0  
**Status:** Production Ready ✅

For detailed documentation, see: `COORDINATOR_PORTAL_GUIDE.md`
