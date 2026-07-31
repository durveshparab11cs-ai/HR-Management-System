# Reports Module - Setup & Integration Guide

## Overview
Comprehensive reporting system with attendance analytics, leave tracking, and payroll insights with filters and visualizations.

**Status**: ✅ Complete (Phase 4 Task 6)

## Features Implemented

### 1. **Reports Dashboard** (`/reports`)
- Year-to-date summary cards
- Attendance percentage
- Remaining leaves count
- YTD earnings display
- Upcoming leaves notification
- Quick access to detailed reports

### 2. **Attendance Report** (`/reports/attendance`)
- Date range filtering (start/end date)
- Attendance percentage calculation
- Detailed breakdown per employee
- Present/Absent/Half-day/Leave statistics
- Color-coded status indicators
- Pagination support

### 3. **Leave Analytics** (`/reports/leave`)
- Leave balance overview by type
- Usage percentage visualization
- Monthly breakdown by leave type
- Pending vs used leaves
- Color-coded progress indicators

### 4. **Payroll Report** (`/reports/payroll`)
- Date range filtering
- Period-wise salary breakdown
- Gross/Net/Deductions comparison
- Days worked tracking
- Status badges (Draft/Approved/Released)
- Bonus and attendance-based pay

### 5. **Data Models**
- `AttendanceReport`: Employee attendance metrics
- `LeaveAnalytics`: Leave usage and balance
- `PayrollReport`: Salary slip summary
- `DashboardReportSummary`: Key metrics overview
- `ChartDataPoint`: Chart visualization data
- `ReportFilters`: Filter parameters

### 6. **API Integration**
```
GET    /api/v1/reports/dashboard                  → Get dashboard summary
GET    /api/v1/reports/attendance                 → Get attendance data (paginated)
GET    /api/v1/reports/leave-analytics            → Get leave analytics
GET    /api/v1/reports/payroll                    → Get payroll report (paginated)
GET    /api/v1/reports/attendance-chart           → Get chart data for attendance
GET    /api/v1/reports/leave-chart                → Get chart data for leaves
GET    /api/v1/reports/export-csv                 → Export report as CSV
```

## File Structure

```
lib/features/reports/
├── data/
│   ├── models/
│   │   └── report_model.dart           # All report models
│   └── repository/
│       └── report_repository.dart      # API operations
├── presentation/
│   ├── providers/
│   │   └── report_provider.dart        # Riverpod state management
│   └── screens/
│       ├── reports_dashboard_screen.dart    # Dashboard overview
│       ├── attendance_report_screen.dart    # Attendance details
│       ├── leave_analytics_screen.dart      # Leave analytics
│       └── payroll_report_screen.dart       # Payroll details
└── __init__.dart
```

## Route Configuration

Added to `lib/core/router/app_router.dart`:
```dart
GoRoute(path: '/reports', name: 'reports-dashboard', builder: (_) => const ReportsDashboardScreen()),
GoRoute(path: '/reports/attendance', name: 'attendance-report', builder: (_) => const AttendanceReportScreen()),
GoRoute(path: '/reports/leave', name: 'leave-analytics', builder: (_) => const LeaveAnalyticsScreen()),
GoRoute(path: '/reports/payroll', name: 'payroll-report', builder: (_) => const PayrollReportScreen()),
```

## State Management (Riverpod)

### Providers

**dashboardReportProvider**: Fetch YTD summary
```dart
final summary = ref.watch(dashboardReportProvider);
```

**attendanceReportProvider**: Get attendance data with filtering
```dart
final report = ref.watch(attendanceReportProvider({
  'startDate': DateTime(2024, 1, 1),
  'endDate': DateTime(2024, 12, 31),
  'department': 'IT',
  'page': 1,
  'perPage': 20,
}));
```

**leaveAnalyticsProvider**: Get leave analytics by type
```dart
final analytics = ref.watch(leaveAnalyticsProvider('Casual Leave'));
```

**payrollReportProvider**: Get payroll data with date range
```dart
final payroll = ref.watch(payrollReportProvider({
  'startDate': DateTime(2024, 1, 1),
  'endDate': DateTime.now(),
  'page': 1,
  'perPage': 20,
}));
```

**attendanceChartProvider**: Chart data for attendance trends
```dart
final chartData = ref.watch(attendanceChartProvider({
  'startDate': DateTime(2024, 1, 1),
  'endDate': DateTime.now(),
}));
```

**leaveChartProvider**: Chart data for leave usage
```dart
final chartData = ref.watch(leaveChartProvider(leaveType));
```

**reportFilterProvider**: Filter state management
- `setDateRange(start, end)`: Update date range
- `setDepartment(dept)`: Set department filter
- `setReportType(type)`: Change report type
- `setPage(page)`: Pagination
- `clearFilters()`: Reset all filters

**reportExportProvider**: Export functionality
- `exportToCSV()`: Export report as CSV

## UI/UX Features

### ReportsDashboardScreen
- **Summary Cards**: Horizontal scrollable metrics
  - Attendance percentage with color
  - Remaining leaves count
  - YTD earnings (formatted in lakhs)
  - Upcoming leaves
- **Report Options**: Card-based navigation
  - Attendance Report
  - Leave Analytics
  - Payroll Report
  - Performance Overview (placeholder)

### AttendanceReportScreen
- **Date Range Filter**: Custom date picker
- **Attendance Trend Chart**: Placeholder for chart integration
- **Details Table**: Employee-wise attendance breakdown
  - Present, Absent, Half-day, Leaves counts
  - Color-coded attendance percentage

### LeaveAnalyticsScreen
- **Leave Type Cards**: Per leave type breakdown
- **Progress Indicator**: Visual leave usage
- **Statistics**: Total, Used, Remaining
- **Monthly Breakdown**: Month-wise usage

### PayrollReportScreen
- **Date Range Filter**: Period selection
- **Payroll Details**: Period-wise breakdown
  - Gross, Deductions, Net salary
  - Bonus and attendance-based pay
  - Status badges

## Color Scheme

| Element | Color |
|---------|-------|
| Primary (Charts) | AppTheme.primary (Blue) |
| Success/Good | AppTheme.success (Green) |
| Warning | Orange |
| Error/Critical | AppTheme.error (Red) |
| Attendance >90% | Green |
| Attendance 75-90% | Orange |
| Attendance <75% | Red |

## Query Parameters & Filtering

### Date Filtering
- `startDate`: ISO format date string (YYYY-MM-DD)
- `endDate`: ISO format date string (YYYY-MM-DD)
- Default range: Last 30 days for attendance, 90 days for payroll

### Department Filtering
- `department`: Department name or ID
- Optional parameter

### Pagination
- `page`: Page number (default: 1)
- `perPage`: Items per page (default: 20)
- Returns: `total`, `page`, `per_page`, `total_pages`

### Report Type
- attendance
- leave
- payroll
- dashboard

## Chart Integration (Placeholder)

Current implementation shows placeholder for charts. To add actual charts:

```dart
// Add dependency
dependencies:
  fl_chart: ^0.69.0

// Implement chart widget
import 'package:fl_chart/fl_chart.dart';

// Replace placeholder with actual chart
LineChart(
  LineChartData(
    lineBarsData: [
      LineChartBarData(spots: chartDataPoints),
    ],
  ),
)
```

## Testing Scenarios

### Dashboard View
1. Open Reports → See summary cards
2. Verify YTD calculations
3. Check upcoming leaves count

### Attendance Report
1. Select custom date range
2. View attendance breakdown
3. Filter by department (if implemented)
4. Verify color coding

### Leave Analytics
1. View all leave types
2. Check usage percentages
3. Verify monthly breakdown
4. Confirm calculations

### Payroll Report
1. Select period
2. View salary breakdown
3. Check status badges
4. Verify bonus/attendance pay display

## Integration Checklist

- [x] Models with JSON serialization
- [x] Repository with pagination
- [x] Riverpod providers & state
- [x] Dashboard screen with summary
- [x] Attendance report screen
- [x] Leave analytics screen
- [x] Payroll report screen
- [x] Date range filtering
- [x] Status indicators & color coding
- [x] Routes configured
- [ ] Chart visualization (ready for fl_chart)
- [ ] CSV export (ready for implementation)
- [ ] Advanced filtering (department, etc.)

## Backend API Requirements

### Response Format Examples

**Get Dashboard Summary**
```json
GET /api/v1/reports/dashboard

{
  "attendance_percentage": 92.5,
  "leaves_remaining": 12,
  "ytd_earnings": 523000,
  "upcoming_leaves": 3,
  "current_status": "Present",
  "last_updated": "2024-08-31T10:30:00"
}
```

**Get Attendance Report**
```json
GET /api/v1/reports/attendance?start_date=2024-08-01&end_date=2024-08-31

{
  "items": [
    {
      "employee_id": 1,
      "employee_name": "John Doe",
      "employee_code": "EMP001",
      "total_days": 22,
      "present_days": 20,
      "absent_days": 1,
      "half_days": 1,
      "leave_days": 0,
      "attendance_percentage": 90.9,
      "report_date": "2024-08-31",
      "department": "IT",
      "designation": "Software Engineer"
    }
  ],
  "total": 45,
  "page": 1,
  "per_page": 20,
  "total_pages": 3
}
```

**Get Leave Analytics**
```json
GET /api/v1/reports/leave-analytics

[
  {
    "total_leave_balance": 20,
    "leave_used": 8,
    "leave_remaining": 12,
    "leave_type": "Casual Leave",
    "usage_percentage": 40.0,
    "breakdown": [
      {
        "month": "January",
        "used": 2,
        "pending": 0
      },
      {
        "month": "February",
        "used": 1,
        "pending": 1
      }
    ]
  }
]
```

## Performance Considerations

- **Pagination**: Use page/perPage for large datasets
- **Date Ranges**: Limit to max 12 months for performance
- **Caching**: Implement provider caching for summary data
- **Lazy Loading**: Load charts only when needed

## Future Enhancements

1. **Chart Integration** (fl_chart)
   - Line charts for attendance trends
   - Pie charts for leave distribution
   - Bar charts for payroll comparison

2. **Advanced Filtering**
   - Department selection
   - Designation filter
   - Custom date ranges
   - Status filters

3. **Export Features**
   - CSV export with formatting
   - PDF reports with branding
   - Email scheduling

4. **Comparison Features**
   - Month-to-month comparison
   - Year-over-year trends
   - Peer comparison (anonymized)

5. **Performance Reports**
   - KPI dashboard
   - Bonus calculation
   - Promotion eligibility

## Dependencies

**Already in pubspec.yaml**:
- flutter_riverpod
- go_router
- dartz
- dio

**Optional (for charts)**:
```yaml
dependencies:
  fl_chart: ^0.69.0
  intl: ^0.19.0
```

**Optional (for PDF/Export)**:
```yaml
dependencies:
  pdf: ^3.10.0
  csv: ^6.0.0
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Empty report | Check date range and data availability |
| Wrong calculations | Verify backend calculation logic |
| Pagination not working | Ensure page/per_page params sent |
| Filters not applied | Check query param names match backend |
| Slow performance | Add pagination, reduce date range |

## Configuration

No additional configuration needed. Reports module integrates with:
- DioClient for HTTP
- ApiConstants for endpoints
- AppTheme for styling
- Riverpod for state management

## Production Readiness Checklist

- [x] Data models complete
- [x] Repository with error handling
- [x] UI screens implemented
- [x] State management setup
- [x] Routes configured
- [x] Date filtering
- [x] Pagination
- [ ] Chart visualization
- [ ] CSV export
- [ ] Performance tested
- [ ] Security audit
- [ ] Compliance review

## Next Steps

1. **Backend Integration**: Ensure API endpoints match documentation
2. **Chart Implementation**: Add fl_chart package and visualizations
3. **Export Features**: Implement CSV/PDF export
4. **Testing**: Add unit and widget tests
5. **Performance**: Monitor and optimize large datasets
6. **User Feedback**: Gather reports on filters needed
