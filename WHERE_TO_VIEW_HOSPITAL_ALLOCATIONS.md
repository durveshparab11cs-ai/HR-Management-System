# Where to View Hospital Allocations

## Quick Access

### 🏥 **Employee Hospital Allocations Page**
**URL:** `/admin/employee-allocation`

**Navigation:**
1. Login as Admin
2. Go to Admin Dashboard
3. Click "Employee Allocation" card (with GPS icon)

OR

Direct URL: `http://your-domain.com/admin/employee-allocation`

---

## What You Can See

### 📊 **Statistics Dashboard**
- **Total Employees:** All employees in system
- **Allocated:** Employees assigned to hospitals
- **Unallocated:** Employees without hospital assignment
- **Flexible Shift:** Employees with flexible working hours

### 👥 **Employee Allocation Table**

Shows for each employee:

| Column | Description |
|--------|-------------|
| **Emp Code** | Employee code (e.g., E-1104001) |
| **Name** | Employee full name |
| **Hospital** | Allocated hospital name and location |
| **Current Shift** | Shift type (Morning/Evening/Night/Flexible) |
| **Shift Time** | Start and end times |
| **Type** | Flexible or Fixed shift indicator |
| **Req. Hours** | Required working hours (default: 9h) |
| **GPS** | GPS validation status (✓ or —) |

### 🔍 **Filter Options**

**Search Employee:**
- Search by employee code or name

**Filter by Hospital:**
- Select specific hospital from dropdown
- Shows all hospitals (Head Office, Claim Department, etc.)

**Filter by Shift Type:**
- All Shifts
- Flexible Shift
- Fixed Shift
- Morning Shift
- Evening Shift
- Night Shift

### 📄 **Pagination**
- 50 employees per page
- Easy navigation between pages

---

## Example: Head Office Employees

To see all employees allocated to **Head Office** with coordinates **19.014847, 72.8452**:

1. Go to `/admin/employee-allocation`
2. In "Hospital" dropdown, select **"Head Office"**
3. Click "Filter"

You will see:
- Employee codes (e.g., E-1104001, E-1507005)
- Employee names
- "Head Office" in Hospital column
- Location: Mumbai Head Office
- GPS icon: ✓ (enabled)

---

## Example: Flexible Shift Employees

To see all employees with flexible working hours:

1. Go to `/admin/employee-allocation`
2. In "Shift Type" dropdown, select **"Flexible Shift"**
3. Click "Filter"

You will see:
- Badge: "Flexible" (green)
- Type column shows: Flexible icon
- These employees are never marked late
- Attendance based on 9+ working hours

---

## Example: Claim Department Employees

To see employees at **Claim Department** (coordinates 19.014847, 72.8452):

1. Go to `/admin/employee-allocation`
2. In "Hospital" dropdown, select **"Claim Department"**
3. Click "Filter"

Result: All claim team members with their shift details.

---

## Other Views

### 🏥 **Hospitals List**
**URL:** `/admin/hospitals`

Shows all hospitals with:
- Hospital name
- Location
- GPS coordinates (Latitude, Longitude)
- Radius (meters)
- Status (Active/Inactive)
- Employee count per hospital

### 📥 **Import Page**
**URL:** `/admin/employee-allocation/import`

Upload Excel file to bulk-assign employees to hospitals.

---

## Quick Links from Admin Dashboard

After login, the Admin Dashboard shows these cards:

1. **🏥 Hospitals** → Manage hospital locations & GPS
2. **📍 Employee Allocation** → View hospital & shift assignments *(THIS IS WHAT YOU NEED)*
3. **⏰ Assign Shifts** → Bulk shift assignment
4. **👤 Employee Master** → View all employee records

---

## For Individual Employee

To see a specific employee's hospital allocation:

### Option 1: Search in Allocation Page
1. Go to `/admin/employee-allocation`
2. Type employee code or name in search box
3. Click "Filter"

### Option 2: Via SQL Query
```sql
SELECT 
    e.employee_code,
    e.name,
    h.hospital_name,
    h.location,
    h.latitude,
    h.longitude,
    e.current_shift,
    e.shift_start_time,
    e.shift_end_time,
    e.is_flexible_shift,
    e.required_working_hours
FROM employee e
LEFT JOIN hospitals h ON e.hospital_id = h.id
WHERE e.employee_code = 'E-1104001';
```

---

## GPS Validation Check

To verify if an employee's hospital GPS is working:

1. **View Allocation:**
   - Go to `/admin/employee-allocation`
   - Find the employee
   - Look at "GPS" column:
     - ✅ Green check = Hospital GPS enabled
     - — Gray dash = Using office GPS fallback

2. **Check Coordinates:**
   - Go to `/admin/hospitals`
   - Find the hospital (e.g., "Head Office")
   - Verify coordinates: **19.014847, 72.8452**
   - Check radius: **100 meters** (recommended)

3. **Test Attendance:**
   - Employee must be within 100m of hospital coordinates
   - System logs will show: "GPS validation using hospital reference: Head Office"

---

## Summary

✅ **Main Page:** `/admin/employee-allocation`  
✅ **Shows:** Employee code, name, hospital, shift, GPS status  
✅ **Filters:** Search, hospital, shift type  
✅ **Head Office Coordinates:** 19.014847, 72.8452  
✅ **Claim Department Coordinates:** 19.014847, 72.8452  

**Access:** Admin login → Admin Dashboard → Click "Employee Allocation" card

---

## Screenshots Reference

Your current view shows "Employee Master" which is different. 

The **Employee Allocation** page will show an additional "Hospital" column that the Employee Master doesn't have.

Navigate to the "Employee Allocation" card in the admin dashboard to see the hospital assignments.

---

## Next Steps

1. **Run Migration:**
   ```bash
   psql $DATABASE_URL -f migrations/add_hospital_allocation.sql
   ```

2. **Create Head Office Hospital:**
   - URL: `/admin/hospitals/add`
   - Name: Head Office
   - Location: Mumbai Head Office
   - Latitude: 19.014847
   - Longitude: 72.8452
   - Radius: 100

3. **Import Hospitals:**
   - URL: `/admin/hospitals/import`
   - Upload: `HOSIPTALS DETAILS.xlsx`

4. **Import Employee Allocations:**
   - URL: `/admin/employee-allocation/import`
   - Upload: `employee master full upload.xlsx`

5. **View Results:**
   - URL: `/admin/employee-allocation`
   - Filter by hospital to verify allocations

---

**Need Help?** Check the deployment guide: `HOSPITAL_ALLOCATION_DEPLOYMENT_GUIDE.md`
