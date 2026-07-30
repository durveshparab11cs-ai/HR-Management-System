# 🗺️ Navigation Guide: How to View Hospital Allocations

## The Page You're Looking For

### **Employee Allocation Page** *(Not Employee Master!)*

---

## 📍 Step-by-Step Navigation

### From Login:

```
1. Login as Admin
   ↓
2. You see: Admin Dashboard
   ↓
3. Look for this card:
   
   ┌─────────────────────────┐
   │    📍 GPS Icon          │
   │  Employee Allocation    │
   │  View hospital & shift  │
   │     assignments         │
   └─────────────────────────┘
   
   ↓
4. Click on "Employee Allocation" card
   ↓
5. You're now on: /admin/employee-allocation
```

---

## What You'll See

### **Employee Allocation Page Layout:**

```
┌────────────────────────────────────────────────────────────────┐
│  👥 Employee Hospital Allocation      [Import Allocations]     │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 Statistics:                                                 │
│  ┌─────────┬─────────┬─────────┬─────────┐                   │
│  │ Total   │ Allocated│ Unall.  │Flexible │                   │
│  │  353    │   250    │  103    │   45    │                   │
│  └─────────┴─────────┴─────────┴─────────┘                   │
│                                                                 │
│  🔍 Filters:                                                    │
│  [Search: EMP-001]  [Hospital: Head Office ▼]  [Shift: All ▼] │
│                                                                 │
│  📋 Employee List:                                              │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │Code   │Name      │Hospital       │Shift   │Time   │GPS   │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │E-1104 │John Doe  │Head Office   │Morning │10-7pm │ ✓    │ │
│  │       │          │Mumbai HO      │        │       │      │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │E-1507 │Jane Smith│Claim Dept    │Flexible│  —    │ ✓    │ │
│  │       │          │Mumbai Claim   │        │       │      │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

---

## Difference from Employee Master

### ❌ **Employee Master** (The page you showed in screenshot)
- URL: `/admin/employee-master`
- Shows: Code, Name, Department, Designation, Registration Status
- **Does NOT show:** Hospital allocation

### ✅ **Employee Allocation** (The page you need)
- URL: `/admin/employee-allocation`
- Shows: Code, Name, **Hospital**, Shift, GPS Status
- **Shows:** Hospital allocation with coordinates

---

## Quick Access URLs

After deployment, you can access these pages directly:

### 🏥 **Hospitals Management**
```
http://your-domain.com/admin/hospitals
```
- View all hospitals
- See coordinates (19.014847, 72.8452)
- Add/edit hospitals

### 📍 **Employee Allocation**
```
http://your-domain.com/admin/employee-allocation
```
- View which employees are allocated to which hospitals
- Filter by hospital
- See GPS status

### 📥 **Import Hospitals**
```
http://your-domain.com/admin/hospitals/import
```
- Upload `HOSIPTALS DETAILS.xlsx`

### 📥 **Import Employee Allocations**
```
http://your-domain.com/admin/employee-allocation/import
```
- Upload `employee master full upload.xlsx`

---

## Find Head Office Employees

### Method 1: Using Filters
1. Go to `/admin/employee-allocation`
2. Click "Hospital" dropdown
3. Select "Head Office"
4. Click "Filter" button
5. Result: All Head Office employees

### Method 2: Using Search
1. Go to `/admin/employee-allocation`
2. Type employee code in search box
3. Click "Filter"
4. See that employee's hospital

---

## Admin Dashboard Cards

Your admin dashboard will now show these cards in **2 rows**:

### **Row 1:**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ 🏥 Hospitals│📍 Employee  │⏰ Assign    │👤 Employee  │
│             │  Allocation │   Shifts    │   Master    │
│ Manage GPS  │View assign. │Bulk assign  │View records │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

### **Row 2:**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ 📊 Import   │⚙️ Office   │📅 Leave     │🔒 User      │
│  Employees  │  Settings   │  Approvals  │Management   │
│Bulk import  │Configure    │Review       │Manage users │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

**Click the second card in Row 1** → "📍 Employee Allocation"

---

## Visual Guide: What Each Page Shows

### 1️⃣ **Hospitals List** (`/admin/hospitals`)
```
Hospital Name      | Location        | Coordinates      | Radius | Employees
───────────────────┼─────────────────┼──────────────────┼────────┼──────────
Head Office        | Mumbai HO       | 19.015, 72.845   | 100m   | 120
Claim Department   | Mumbai Claim    | 19.015, 72.845   | 100m   | 45
ABC Hospital       | Pune            | 18.520, 73.857   | 150m   | 88
```

### 2️⃣ **Employee Allocation** (`/admin/employee-allocation`)
```
Emp Code  | Name        | Hospital       | Shift      | Type      | GPS
──────────┼─────────────┼────────────────┼────────────┼───────────┼─────
E-1104001 | John Doe    | Head Office    | Morning    | Fixed     | ✓
E-1507005 | Jane Smith  | Claim Dept     | Flexible   | Flexible  | ✓
E-1801019 | Bob Wilson  | ABC Hospital   | Night      | Fixed     | ✓
E-1801020 | Alice Brown | (Not Allocated)| —          | —         | —
```

### 3️⃣ **Employee Master** (`/admin/employee-master`)
```
Code      | Name        | Department     | Designation | Status
──────────┼─────────────┼────────────────┼─────────────┼──────────
E-1104001 | John Doe    | IT             | Developer   | Registered
E-1507005 | Jane Smith  | Claims         | Manager     | Pending
```

**Notice:** Employee Master does NOT show hospital!

---

## Summary

🎯 **What you need:** Employee Allocation page  
📍 **URL:** `/admin/employee-allocation`  
🚀 **How to get there:** Admin Dashboard → Click "Employee Allocation" card (Row 1, Card 2)  
✅ **Shows:** Hospital assignments with GPS coordinates  

🔴 **What you DON'T need:** Employee Master page  
❌ **URL:** `/admin/employee-master`  
❌ **Doesn't show:** Hospital allocations  

---

## Current Status

⏳ **Not deployed yet** - You need to:

1. Run database migration
2. Create hospitals (Head Office, Claim Department)
3. Import hospital data from Excel
4. Import employee allocations from Excel
5. **Then** you can view allocations on `/admin/employee-allocation`

---

## After Deployment

Once you complete the steps above, you'll be able to:

✅ See which employees work at Head Office (19.014847, 72.8452)  
✅ See which employees work at Claim Department (19.014847, 72.8452)  
✅ See which employees have flexible shifts  
✅ Filter employees by hospital  
✅ Verify GPS coordinates for each location  

**All visible on:** `/admin/employee-allocation` page

---

**Ready to deploy?** Follow `HOSPITAL_ALLOCATION_DEPLOYMENT_GUIDE.md`
