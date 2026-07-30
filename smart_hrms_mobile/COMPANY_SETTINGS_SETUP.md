# Company/Hospital Settings Module - Setup & Integration Guide

## Overview
Comprehensive company/hospital information system with department management, designations, and employee allocation tracking.

**Status**: ✅ Complete (Phase 4 Task 7)

## Features Implemented

### 1. **Company Information** (`/company`)
- Hospital/Company profile display
- Organization statistics (employees, departments, avg salary)
- Contact information
- Address and registration details
- Banking information
- Logo display with fallback

### 2. **Departments Management** (`/company/departments`)
- List all departments with employee count
- Department manager information
- Budget tracking
- Activity status (Active/Inactive)
- Department details navigation

### 3. **Designations/Job Titles** (`/company/designations`)
- Browse all designations
- Filter by department
- Employee count per designation
- Salary grade tracking
- Department assignment

### 4. **Employee Allocation**
- Current department and designation
- Manager assignment
- Allocation date tracking
- Allocation history
- Transfer tracking

### 5. **Data Models**
- `Company`: Hospital/organization profile
- `Department`: Department information
- `Designation`: Job title and level
- `EmployeeAllocation`: Current assignment
- `AllocationHistory`: Transfer history
- `CompanyStatistics`: Organization metrics

### 6. **API Integration**
```
GET    /api/v1/company/info                       → Get company profile
GET    /api/v1/company/statistics                 → Get company statistics
GET    /api/v1/company/departments                → Get all departments
GET    /api/v1/company/departments/{id}           → Get department details
GET    /api/v1/company/departments/{id}/employees → Get dept employees
GET    /api/v1/company/designations               → Get designations
GET    /api/v1/company/designations/{id}          → Get designation details
GET    /api/v1/company/allocations/{empId}        → Get employee allocation
GET    /api/v1/company/allocations/{empId}/history → Get allocation history
POST   /api/v1/company/allocations/{empId}/update → Update allocation (admin)
```

## File Structure

```
lib/features/company/
├── data/
│   ├── models/
│   │   └── company_model.dart          # All company-related models
│   └── repository/
│       └── company_repository.dart     # API operations
├── presentation/
│   ├── providers/
│   │   └── company_provider.dart       # Riverpod state management
│   └── screens/
│       ├── company_info_screen.dart    # Company profile
│       ├── departments_screen.dart     # Departments list
│       └── designations_screen.dart    # Designations list
└── __init__.dart
```

## Route Configuration

Added to `lib/core/router/app_router.dart`:
```dart
GoRoute(path: '/company', name: 'company-info', builder: (_) => const CompanyInfoScreen()),
GoRoute(path: '/company/departments', name: 'departments', builder: (_) => const DepartmentsScreen()),
GoRoute(path: '/company/designations', name: 'designations', builder: (_) => const DesignationsScreen()),
```

## State Management (Riverpod)

### Providers

**companyInfoProvider**: Get company profile
```dart
final info = ref.watch(companyInfoProvider);
```

**companyStatisticsProvider**: Get organization metrics
```dart
final stats = ref.watch(companyStatisticsProvider);
```

**departmentsProvider**: Get all departments
```dart
final departments = ref.watch(departmentsProvider);
```

**designationsProvider**: Get designations with optional filter
```dart
final designations = ref.watch(designationsProvider(departmentId));
```

**employeeAllocationProvider**: Get current employee allocation
```dart
final allocation = ref.watch(employeeAllocationProvider(employeeId));
```

**allocationHistoryProvider**: Get employee transfer history
```dart
final history = ref.watch(allocationHistoryProvider(employeeId));
```

**departmentDetailsProvider**: Get department with employees
```dart
final dept = ref.watch(departmentDetailsProvider(deptId));
```

**designationDetailsProvider**: Get designation details
```dart
final design = ref.watch(designationDetailsProvider(designId));
```

**companyActionProvider**: Action state (update allocation)
- `updateEmployeeAllocation()`: Change employee department/designation (admin)
- `clearMessages()`: Clear notifications

## UI/UX Features

### CompanyInfoScreen
- **Statistics Card Bar**: Horizontal scrollable metrics
  - Total employees
  - Active employees
  - Total departments
  - Average salary
- **Company Header**: Logo, name, industry type
- **Sections**:
  - Contact Information (email, phone, website)
  - Address Information (street, city, state, country)
  - Registration Details (reg number, tax ID, established date)
  - Banking Information (bank name, account last 4 digits)

### DepartmentsScreen
- **Department Cards**:
  - Department icon and name
  - Manager name
  - Employee count badge
  - Description
  - Budget information
  - Active/Inactive status
  - Click to view details

### DesignationsScreen
- **Filter Bar**: Department-wise filtering
  - "All" option to show all designations
  - Individual department chips
- **Designation Cards**:
  - Job title with icon
  - Department assignment
  - Employee count
  - Description
  - Salary grade badge
  - Active/Inactive status

## Color Scheme

| Element | Color |
|---------|-------|
| Primary | AppTheme.primary (Blue) |
| Secondary | AppTheme.secondary (Purple) |
| Success/Active | AppTheme.success (Green) |
| Error/Inactive | AppTheme.error (Red) |
| Warning | Orange |

## Statistics Metrics

- **Total Employees**: Count of all employees
- **Active Employees**: Count of active status
- **Inactive Employees**: Count of inactive status
- **Total Departments**: Count of departments
- **Total Designations**: Count of designations
- **Average Salary**: YTD average employee salary
- **Total Leave Balance**: Company-wide leave balance
- **Attendance Percentage**: Overall attendance rate

## Company Information Fields

| Field | Type | Required | Format |
|-------|------|----------|--------|
| Name | String | Yes | Company/Hospital name |
| Registration Number | String | Yes | Legal registration |
| Industry Type | String | Yes | Hospital/IT/etc |
| Address | String | Yes | Street address |
| City | String | Yes | City name |
| State | String | Yes | State/Province |
| Country | String | No | Country name |
| Postal Code | String | No | Postal/ZIP code |
| Phone | String | No | +XX XXXXXXXXXX |
| Email | String | No | email@company.com |
| Website | String | No | https://website.com |
| Tax ID | String | No | TIN/GST number |
| Bank Account | String | No | Masked: ****XXXX |
| Bank Name | String | No | Bank name |

## Department Fields

- Name (required)
- Description (optional)
- Manager ID and Name
- Employee count
- Budget (optional)
- Active status
- Created date

## Designation Fields

- Title (required)
- Description (optional)
- Department ID and name
- Reporting To (manager)
- Salary Grade
- Employee count
- Active status

## Employee Allocation Fields

- Employee ID, Name, Code
- Department (current and assigned)
- Designation (current and assigned)
- Manager ID and Name
- Allocation date
- Deallocation date (if transferred)
- Status (active/inactive/transferred)
- Remarks

## Testing Scenarios

### Company Profile View
1. Open Company → See all metrics
2. Verify statistics calculations
3. Check logo display
4. Review all information sections

### Departments Browsing
1. Open Departments → See all depts
2. Click department → View details
3. Verify employee count
4. Check manager assignment

### Designations Browse
1. Open Designations → See all
2. Filter by department → Updates list
3. Check salary grades
4. Verify employee count

### Employee Allocation
1. Get employee allocation → Shows current
2. View allocation history → Shows transfers
3. Check manager assignment
4. Review dates

## Integration Checklist

- [x] Models with JSON serialization
- [x] Repository with all API calls
- [x] Riverpod providers & state
- [x] Company info screen with stats
- [x] Departments list screen
- [x] Designations list with filtering
- [x] Routes configured
- [x] Error handling & validation
- [x] Status indicators
- [ ] Employee allocation update (admin)
- [ ] Department member browsing
- [ ] Transfer history UI

## Backend API Requirements

### Response Format Examples

**Get Company Info**
```json
GET /api/v1/company/info

{
  "id": 1,
  "name": "Apollo Hospitals",
  "registration_number": "REG123456",
  "industry_type": "Hospital",
  "logo": "https://example.com/logo.png",
  "address": "123 Medical Street",
  "city": "Bangalore",
  "state": "Karnataka",
  "country": "India",
  "postal_code": "560001",
  "phone": "+91 9876543210",
  "email": "info@apollo.com",
  "website": "https://apollo.com",
  "established_date": "1983-01-01",
  "total_employees": 450,
  "tax_id": "GSTIN123456",
  "bank_name": "ICICI Bank",
  "bank_account_number": "****5678",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Get Departments**
```json
GET /api/v1/company/departments

[
  {
    "id": 1,
    "name": "Emergency",
    "description": "Emergency and Casualty",
    "manager_id": 5,
    "manager_name": "Dr. Rajesh Kumar",
    "employee_count": 45,
    "budget": "5000000",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

**Get Statistics**
```json
GET /api/v1/company/statistics

{
  "total_employees": 450,
  "active_employees": 420,
  "inactive_employees": 30,
  "total_departments": 12,
  "total_designations": 35,
  "average_salary": 650000,
  "total_leave_balance": 3600,
  "attendance_percentage": 94
}
```

## Future Enhancements

1. **Department Management**
   - Create/Edit departments (admin)
   - Manage department budget
   - Assign/change managers

2. **Designation Management**
   - Create designations
   - Set salary grades
   - Define reporting hierarchy

3. **Employee Transfers**
   - Initiate transfers
   - Approval workflow
   - Historical tracking

4. **Organization Chart**
   - Visual hierarchy
   - Reporting structure
   - Team breakdown

5. **Reports**
   - Department analytics
   - Designation distribution
   - Org structure export

## Dependencies

**Already in pubspec.yaml**:
- flutter_riverpod
- go_router
- dartz
- dio

## Configuration

No additional configuration needed. Company module integrates with:
- DioClient for HTTP
- ApiConstants for endpoints
- AppTheme for styling
- Riverpod for state management

## Production Readiness

- [x] Data models complete
- [x] Repository with error handling
- [x] UI screens implemented
- [x] State management setup
- [x] Routes configured
- [x] Statistics display
- [x] Error handling
- [ ] Admin allocation update
- [ ] Performance tested
- [ ] Security audit

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No departments shown | Check /company/departments endpoint |
| Statistics incorrect | Verify backend calculation |
| Logo not loading | Check CORS headers, image URL |
| Filter not working | Ensure department filter params correct |

## Next Steps

1. **Backend Integration**: Ensure all API endpoints match documentation
2. **Admin Features**: Add allocation update functionality
3. **Organization Chart**: Implement visual hierarchy
4. **Transfer Workflow**: Add approval process
5. **Testing**: Add comprehensive tests
6. **Performance**: Optimize for large organizations
