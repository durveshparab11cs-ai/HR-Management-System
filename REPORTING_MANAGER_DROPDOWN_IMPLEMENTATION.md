# Reporting Manager Searchable Dropdown - Implementation Summary

## Overview
Successfully implemented a searchable dropdown for Reporting Manager selection across all leave request types (Leave, Half Day, Early Leave) in the Smart HRMS system.

---

## ✅ Changes Made

### 1. **Forms Update** (`app/blueprints/leave/forms.py`)

#### Added Predefined Managers List:
```python
REPORTING_MANAGERS = [
    ("Ekta Sunil More", "Ekta Sunil More"),
    ("Pallavi Mangesh Mali", "Pallavi Mangesh Mali"),
    ("Prasad Morje", "Prasad Morje"),
    ("Rutuja Suresh Pawar", "Rutuja Suresh Pawar"),
    ("Sampada Arvind Thakur", "Sampada Arvind Thakur"),
    ("Sanam Desai", "Sanam Desai"),
    ("Shubham Sanjay Pednekar", "Shubham Sanjay Pednekar"),
    ("Tejas Ashok Jadhav", "Tejas Ashok Jadhav"),
    ("Umesh Pradeep Devare", "Umesh Pradeep Devare"),
    ("Vijay Shankar Manjare", "Vijay Shankar Manjare"),
    ("Akshay Darsharth Ghadi", "Akshay Darsharth Ghadi"),
    ("Aditya Nivas Mayekar", "Aditya Nivas Mayekar"),
    ("Durvesh Parab", "Durvesh Parab"),
    ("Sakshi Jadhav", "Sakshi Jadhav"),
    ("Pratik Dinkar Mohite", "Pratik Dinkar Mohite"),
    ("Sakshi Anil Yeram", "Sakshi Anil Yeram"),
    ("Atharva Bhosale", "Atharva Bhosale"),
]
```

#### Replaced Forms Fields:
- **Before:** `reporting_manager_code = StringField(...)`
- **After:** `reporting_manager = SelectField(choices=[], ...)`

**Updated Forms:**
- `ApplyLeaveForm`
- `ApplyHalfDayForm`
- `ApplyEarlyLeaveForm`

---

### 2. **Routes Update** (`app/blueprints/leave/routes.py`)

#### Added Helper Function:
```python
def _get_manager_code_by_name(manager_name: str) -> str:
    """Look up manager's employee code from employee_master by name."""
    master = EmployeeMaster.query.filter_by(
        employee_name=manager_name,
        is_active=True
    ).first()
    return master.employee_code if master else ""
```

#### Updated Routes:
**1. Apply Leave Route:**
```python
@leave_bp.route("/apply", methods=["GET", "POST"])
def apply():
    form.reporting_manager.choices = get_manager_choices()
    
    if form.validate_on_submit():
        manager_name = form.reporting_manager.data
        manager_code = _get_manager_code_by_name(manager_name)
        
        _svc.apply_leave(employee_id=emp.id, form_data={
            ...
            "reporting_manager_name": manager_name,
            "reporting_manager_code": manager_code or "",
        })
```

**2. Apply Half Day Route:** (Same pattern)
**3. Apply Early Leave Route:** (Same pattern)

**4. My Approvals Route (Manager Dashboard):**
```python
@leave_bp.route("/my-approvals")
def my_approvals():
    # Get manager's name from employee_master
    manager_master = EmployeeMaster.query.filter_by(
        employee_code=emp.employee_code.upper(),
        is_active=True
    ).first()
    
    mgr_name = manager_master.employee_name
    
    # Filter by both name AND code (backward compatibility)
    lr_q = LeaveRequest.query.filter(
        or_(
            LeaveRequest.reporting_manager_name == mgr_name,
            LeaveRequest.reporting_manager_code == mgr_code
        ),
        LeaveRequest.is_deleted == False
    )
```

---

### 3. **Repository Update** (`app/blueprints/leave/repository.py`)

#### Added New Methods:

```python
def get_halfdays_for_manager_by_name(self, mgr_name: str, page=1, per_page=30, status=""):
    """Return half-day requests where the manager is identified by name."""
    q = HalfDayRequest.query.filter(
        HalfDayRequest.reporting_manager_name == mgr_name,
        HalfDayRequest.is_deleted == False
    )
    if status:
        q = q.filter_by(status=status)
    return q.order_by(HalfDayRequest.applied_on.desc()).paginate(...)

def get_earlyleaves_for_manager_by_name(self, mgr_name: str, page=1, per_page=30, status=""):
    """Return early-leave requests where the manager is identified by name."""
    q = EarlyLeaveRequest.query.filter(
        EarlyLeaveRequest.reporting_manager_name == mgr_name,
        EarlyLeaveRequest.is_deleted == False
    )
    if status:
        q = q.filter_by(status=status)
    return q.order_by(EarlyLeaveRequest.applied_on.desc()).paginate(...)
```

---

### 4. **Templates Update**

#### A. **Leave Application** (`app/templates/leave/apply.html`)

**Before:**
```html
<input type="text" name="reporting_manager_code" id="lr-mgr-code"
       placeholder="e.g. E-2603028" autocomplete="off">
```

**After:**
```html
<select name="reporting_manager" id="reporting-manager-select" class="form-select">
    <option value="">-- Select Reporting Manager --</option>
    <option value="Ekta Sunil More">Ekta Sunil More</option>
    <option value="Pallavi Mangesh Mali">Pallavi Mangesh Mali</option>
    <!-- ... all 17 managers ... -->
</select>
```

**Added Select2:**
```html
<!-- CSS -->
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
<link href="https://cdn.jsdelivr.net/npm/select2-bootstrap-5-theme@1.3.0/dist/select2-bootstrap-5-theme.min.css" rel="stylesheet" />

<!-- JS -->
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
<script>
$('#reporting-manager-select').select2({
    theme: 'bootstrap-5',
    placeholder: '-- Select Reporting Manager --',
    allowClear: false,
    width: '100%'
});
</script>
```

#### B. **Half Day Application** (`app/templates/leave/apply_halfday.html`)
- Same changes as Leave Application
- Select2 ID: `reporting-manager-select-hd`

#### C. **Early Leave Application** (`app/templates/leave/apply_earlyleave.html`)
- Same changes as Leave Application  
- Select2 ID: `reporting-manager-select-el`

---

## 🔄 Data Flow

### When Employee Applies for Leave:

```
1. Employee selects "Tejas Ashok Jadhav" from dropdown
   ↓
2. Form submits: reporting_manager = "Tejas Ashok Jadhav"
   ↓
3. Routes.py calls _get_manager_code_by_name("Tejas Ashok Jadhav")
   ↓
4. Queries employee_master for matching name
   ↓
5. Returns employee_code (if exists, e.g., "E-2510016")
   ↓
6. Service saves BOTH:
   - reporting_manager_name: "Tejas Ashok Jadhav"
   - reporting_manager_code: "E-2510016"
   ↓
7. Leave status set to "pending"
```

### When Manager Views Leave Approval:

```
1. Manager "Tejas Ashok Jadhav" logs in with code "E-2510016"
   ↓
2. Opens Leave Approval page (/leave/my-approvals)
   ↓
3. System queries employee_master:
   - Gets manager's name: "Tejas Ashok Jadhav"
   ↓
4. Filters leave requests WHERE:
   - reporting_manager_name == "Tejas Ashok Jadhav"
   OR reporting_manager_code == "E-2510016"
   ↓
5. Displays ONLY requests assigned to Tejas
   ↓
6. Manager can Approve/Reject with optional remarks
   ↓
7. Status updated, employee notified
```

---

## 🎯 Key Features Implemented

### ✅ Searchable Dropdown
- **Technology:** Select2.js with Bootstrap 5 theme
- **Features:**
  - Type-ahead search
  - Fuzzy matching
  - Keyboard navigation
  - Mobile-friendly

### ✅ Manager Isolation
- Each manager sees ONLY their assigned requests
- Filtering by both name AND code (backward compatibility)
- No cross-manager visibility

### ✅ Backward Compatibility
- Old requests with only `reporting_manager_code` still work
- System checks both fields when filtering
- No data migration needed

### ✅ Data Integrity
- Stores both manager name and code
- Automatic lookup from employee_master
- Handles cases where manager is not in employee_master

---

## 📊 Database Schema

### Existing Tables Used:
**No new tables created. Reuses existing schema:**

```sql
-- leave_requests table
reporting_manager_name VARCHAR(200)   -- Stores selected name
reporting_manager_code VARCHAR(30)    -- Stores employee code (if found)

-- half_day_requests table
reporting_manager_name VARCHAR(200)
reporting_manager_code VARCHAR(30)

-- early_leave_requests table
reporting_manager_name VARCHAR(200)
reporting_manager_code VARCHAR(30)

-- employee_master table (existing)
employee_code VARCHAR(30)
employee_name VARCHAR(200)
is_active BOOLEAN
```

---

## 🔍 Testing Checklist

### Test Cases:

#### 1. **Employee Submission**
- [ ] Open Apply Leave page
- [ ] Dropdown shows all 17 managers
- [ ] Search works (e.g., type "Tejas" → filters to "Tejas Ashok Jadhav")
- [ ] Select manager
- [ ] Submit form
- [ ] Verify both name and code saved in database

#### 2. **Manager Approval**
- [ ] Login as "Tejas Ashok Jadhav" (E-2510016)
- [ ] Navigate to Leave Approval (/leave/my-approvals)
- [ ] Verify ONLY requests for Tejas are visible
- [ ] Login as another manager
- [ ] Verify they DON'T see Tejas's requests

#### 3. **Half Day & Early Leave**
- [ ] Test same flow for Half Day requests
- [ ] Test same flow for Early Leave requests
- [ ] Verify manager isolation works for all types

#### 4. **Backward Compatibility**
- [ ] Old requests with only `reporting_manager_code` still display
- [ ] Managers can still approve old requests

#### 5. **Edge Cases**
- [ ] Manager not in employee_master → code field empty, name still saved
- [ ] Empty dropdown selection → validation error
- [ ] Multiple managers with similar names → distinct options

---

## 🚀 Deployment Steps

### 1. **Backup Database**
```bash
pg_dump your_database > backup_before_manager_dropdown.sql
```

### 2. **Deploy Code**
```bash
git add .
git commit -m "Implement searchable reporting manager dropdown"
git push origin main
```

### 3. **Verify Deployment**
- Check all three forms render correctly
- Test Select2 functionality
- Verify manager isolation

### 4. **No Migration Needed**
- Uses existing `reporting_manager_name` and `reporting_manager_code` columns
- No schema changes required

---

## 📝 Configuration

### To Add/Remove Managers:

Edit `app/blueprints/leave/forms.py`:

```python
REPORTING_MANAGERS = [
    ("Manager Name", "Manager Name"),
    # Add new managers here
]
```

### To Change Dropdown Styling:

Edit Select2 CSS in templates:

```css
.select2-container .select2-selection--single {
    height: 38px;  /* Adjust height */
    padding: 6px 12px;
}
```

---

## 🔒 Security Considerations

### ✅ Implemented:
1. **CSRF Protection:** All forms include CSRF tokens
2. **Input Validation:** WTForms validators on all fields
3. **SQL Injection:** Using SQLAlchemy ORM (parameterized queries)
4. **Authorization:** Manager can only see their assigned requests
5. **Data Integrity:** Both name and code stored for verification

### ✅ Access Control:
- Employees can only submit for predefined managers
- Managers can only approve requests assigned to them
- No cross-manager visibility

---

## 📞 Support & Troubleshooting

### Common Issues:

**1. Dropdown not searchable:**
- Check if Select2 JS/CSS loaded
- Verify jQuery is available
- Check browser console for errors

**2. Manager sees no requests:**
- Verify manager's name in employee_master matches dropdown exactly
- Check spelling and spacing
- Verify employee_code is correct

**3. Form validation fails:**
- Ensure manager is selected from dropdown
- Check network tab for form submission

**4. Old requests not showing:**
- System filters by BOTH name and code
- Check `reporting_manager_code` field in old records

---

## 📊 SQL Queries for Verification

### Check Leave Assignments:
```sql
SELECT 
    lr.id,
    e.employee_code AS applicant_code,
    em.employee_name AS applicant_name,
    lr.reporting_manager_name,
    lr.reporting_manager_code,
    lr.status,
    lr.applied_on
FROM leave_requests lr
JOIN employee e ON lr.employee_id = e.id
LEFT JOIN employee_master em ON e.employee_code = em.employee_code
WHERE lr.is_deleted = FALSE
ORDER BY lr.applied_on DESC
LIMIT 20;
```

### Check Manager's Requests:
```sql
SELECT 
    COUNT(*) as total_requests,
    status,
    reporting_manager_name
FROM leave_requests
WHERE reporting_manager_name = 'Tejas Ashok Jadhav'
  AND is_deleted = FALSE
GROUP BY status, reporting_manager_name;
```

### Verify Manager Mapping:
```sql
SELECT 
    employee_code,
    employee_name,
    is_active
FROM employee_master
WHERE employee_name IN (
    'Ekta Sunil More',
    'Tejas Ashok Jadhav',
    'Durvesh Parab'
    -- ... all 17 managers
);
```

---

## ✨ Benefits

### For Employees:
- ✅ Easy manager selection (no need to remember codes)
- ✅ Searchable dropdown (type to find)
- ✅ No typing errors
- ✅ Consistent UX across all leave types

### For Managers:
- ✅ See only their assigned requests
- ✅ Clean, organized approval dashboard
- ✅ No access to other managers' requests
- ✅ Automatic notification routing

### For HR/Admin:
- ✅ Centralized manager list
- ✅ Easy to add/remove managers
- ✅ Audit trail (both name and code stored)
- ✅ Backward compatible with old data

---

## 🎉 Implementation Complete!

All leave request forms now use a searchable dropdown for Reporting Manager selection, with proper manager isolation and approval routing.

**Test the feature and verify everything works as expected!**
