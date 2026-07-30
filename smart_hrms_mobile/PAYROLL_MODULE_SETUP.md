# Payroll Module - Setup & Integration Guide

## Overview
Complete payroll system for salary slip generation, viewing, PDF download, and sharing.

**Status**: ✅ Complete (Phase 4 Task 5)

## Features Implemented

### 1. **Employee Salary Information**
- **PayrollListScreen** (`/payroll`): View all salary slips with year-to-date summary
- **PayslipDetailScreen** (`/payroll/{id}`): Detailed salary slip breakdown
- Year-to-date (YTD) summary with earnings and deductions

### 2. **Salary Slip Components**
- **Earnings**: Basic salary, allowances (HRA, DA, Medical, Conveyance, Other)
- **Deductions**: Professional tax, Provident fund, Income tax, Other deductions
- **Attendance**: Days worked, total days, leaves taken
- **Summary**: Gross salary, total deductions, net salary

### 3. **Salary Slip Status Tracking**
- Draft, Approved, Released statuses
- Approval metadata (approved by, date)
- Remarks and comments

### 4. **Data Models**
- `SalarySlip`: Complete salary slip with earnings/deductions breakdown
- `PayrollSummary`: Year-to-date summary and statistics
- `SalarySlipListResponse`: Paginated response

### 5. **API Integration**
```
GET    /api/v1/payroll/payslips                    → Get salary slips (paginated)
GET    /api/v1/payroll/payslips/{id}               → Get specific payslip
GET    /api/v1/payroll/payslips/latest             → Get latest payslip
GET    /api/v1/payroll/payslips/summary            → Get YTD summary
GET    /api/v1/payroll/payslips/{id}/download      → Download PDF
POST   /api/v1/payroll/payslips/{id}/share         → Share via email
GET    /api/v1/payroll/payslips/periods            → Get available periods
```

## File Structure

```
lib/features/payroll/
├── data/
│   ├── models/
│   │   └── payroll_model.dart         # SalarySlip, PayrollSummary
│   └── repository/
│       └── payroll_repository.dart    # API operations
├── presentation/
│   ├── providers/
│   │   └── payroll_provider.dart      # Riverpod state management
│   └── screens/
│       ├── payroll_list_screen.dart   # Salary slip list
│       └── payslip_detail_screen.dart # Detailed slip view
└── __init__.dart
```

## Route Configuration

Added to `lib/core/router/app_router.dart`:
```dart
GoRoute(path: '/payroll', name: 'payroll-list', builder: (_) => const PayrollListScreen()),
GoRoute(
  path: '/payroll/:id',
  name: 'payslip-detail',
  builder: (_, state) => PayslipDetailScreen(payslipId: int.parse(state.pathParameters['id'] ?? '0')),
),
```

## State Management (Riverpod)

### Providers

**payrollSummaryProvider**: Fetch YTD summary
```dart
final summary = ref.watch(payrollSummaryProvider);
```

**latestPayslipProvider**: Fetch latest salary slip
```dart
final latest = ref.watch(latestPayslipProvider);
```

**payslipsProvider**: Paginated salary slips with filtering
```dart
final payslips = ref.watch(payslipsProvider({
  'page': 1,
  'perPage': 20,
  'year': 2024,      // optional
  'month': 8,        // optional
}));
```

**payslipDetailProvider**: Get single payslip
```dart
final slip = ref.watch(payslipDetailProvider(slipId));
```

**availablePeriodsProvider**: Get available year-month combinations
```dart
final periods = ref.watch(availablePeriodsProvider);
```

**payrollActionProvider**: Action state (download/share)
- `downloadPayslip(id)`: Download PDF
- `sharePayslip(id, recipients, message)`: Share via email
- `clearMessages()`: Clear notifications

## UI/UX Features

### PayrollListScreen
- **Summary Card**: Year-to-date statistics
  - Total gross, deductions, net salary
  - Paid months, average monthly salary
  - Gradient background with white text
- **Payslip List**: Clickable cards showing
  - Period (Month Year)
  - Salary breakdown (Gross/Deductions/Net)
  - Status badge (Draft/Approved/Released)
  - Download and Share action buttons
  - Pull-to-refresh support
- **Responsive**: Adapts to different screen sizes

### PayslipDetailScreen
- **Header Card**: Large display of period and status
- **Employment Details**: Name, code, designation, department
- **Earnings Section**: All allowances with subtotal
- **Deductions Section**: All tax/fund deductions with subtotal
- **Attendance**: Working days, leaves taken
- **Summary**: Color-coded salary breakdown
- **Status Information**: Approval metadata and remarks
- **Action Buttons**: Download PDF and Share options

## Color Scheme

| Element | Color |
|---------|-------|
| Primary (Header) | AppTheme.primary |
| Earnings (Earnings items) | AppTheme.success (green) |
| Deductions (Deduction items) | AppTheme.error (red) |
| Net Salary | AppTheme.primary (emphasized) |
| Draft Status | Grey |
| Approved Status | Orange |
| Released Status | Green (AppTheme.success) |

## Salary Calculations

### Gross Salary Formula
```
Gross = Basic + HRA + DA + Conveyance + Medical + Other Allowances
```

### Total Deductions Formula
```
Deductions = Professional Tax + Provident Fund + Income Tax + Other
```

### Net Salary Formula
```
Net = Gross - Deductions
```

### Take-Home Percentage
```
Take-Home % = (Net / Gross) × 100
```

## Testing Scenarios

### Employee Flow
1. Open "Payroll" → View YTD summary and list
2. Tap salary slip → View detailed breakdown
3. Download PDF (future feature)
4. Share via email (future feature)

### Filter & Search
1. Select year/month filters → List updates
2. Pagination working correctly
3. Status filtering (if implemented)

### Error Handling
- Network error → Retry button
- No data → Friendly message
- API timeout → Error notification

## Integration Checklist

- [x] Models created with JSON serialization
- [x] Repository with all API operations
- [x] Riverpod providers & state notifier
- [x] PayrollListScreen with YTD summary
- [x] PayslipDetailScreen with full breakdown
- [x] Routes added to app router
- [x] Error handling & validation
- [x] Pagination support
- [x] Material Design 3 styling
- [ ] PDF download functionality (ready for implementation)
- [ ] Share via email (ready for implementation)

## Backend API Requirements

### Response Format Examples

**Get Payslips List**
```json
GET /api/v1/payroll/payslips?page=1&per_page=20

{
  "items": [
    {
      "id": 1,
      "employee_name": "John Doe",
      "employee_code": "EMP001",
      "designation": "Software Engineer",
      "department": "IT",
      "month": 8,
      "year": 2024,
      "generated_date": "2024-08-01",
      "basic_salary": 50000,
      "dearness_allowance": 5000,
      "house_rent_allowance": 15000,
      "conveyance_allowance": 2000,
      "medical_allowance": 1000,
      "other_allowances": 0,
      "gross_salary": 73000,
      "professional_tax": 200,
      "provident_fund": 5000,
      "income_tax": 4800,
      "other_deductions": 0,
      "total_deductions": 10000,
      "net_salary": 63000,
      "days_worked": 20,
      "total_days": 22,
      "leaves_taken": 1,
      "status": "released",
      "remarks": null,
      "approved_at": "2024-08-05",
      "approved_by": "Manager Name",
      "released_at": "2024-08-10"
    }
  ],
  "total": 12,
  "page": 1,
  "per_page": 20,
  "total_pages": 1
}
```

**Get Payroll Summary**
```json
GET /api/v1/payroll/payslips/summary

{
  "ytd_gross_salary": 584000,
  "ytd_net_salary": 504000,
  "ytd_taxes": 38400,
  "ytd_deductions": 41600,
  "paid_months": 8,
  "total_months": 12,
  "last_payment_date": "2024-08-31",
  "average_monthly_salary": 73000
}
```

## Future Enhancements

### PDF Generation (Phase 4 Task Enhancement)
**Dependencies**:
- `pdf: ^3.10.0` - PDF creation
- `printing: ^5.11.0` - Print/Share functionality

**Implementation Plan**:
```dart
// Generate PDF with salary slip
Future<void> generatePayslipPDF(SalarySlip slip) async {
  final pdf = pw.Document();
  pdf.addPage(
    pw.Page(
      build: (pw.Context context) => _buildPDFContent(slip),
    ),
  );
  // Save to file or share
}
```

### Share Features
- Email with PDF attachment
- WhatsApp/messaging integration
- Cloud storage backup

### Advanced Features
- Payslip history comparison
- Tax calculation optimizer
- Export to accounting software
- Bulk payslip generation
- Email reminders for new slips
- Payslip download history
- Digital signature verification

## Known Limitations

- PDF download not yet implemented (requires `pdf` package)
- Share functionality placeholder only
- No offline payslip viewing
- No email scheduling

## Dependencies

**Already in pubspec.yaml**:
- `flutter_riverpod: ^2.4.0`
- `go_router: ^13.0.0`
- `dartz: ^0.10.1`
- `dio: ^5.3.1`

**To add for PDF features** (optional):
```yaml
dependencies:
  pdf: ^3.10.0
  printing: ^5.11.0
  path_provider: ^2.1.0
```

## Configuration

No additional configuration needed. Payroll module integrates seamlessly with existing:
- DioClient for HTTP
- ApiConstants for endpoints
- AppTheme for styling
- Auth flow for user context

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Payslips not loading | Check backend `/payroll/payslips` endpoint |
| Status not showing | Ensure backend returns `status` field |
| Calculations off | Verify backend calculation logic |
| Pagination not working | Check `page`, `per_page` parameters |

## Next Steps

1. **Backend Integration**: Ensure Flask endpoints match API constants
2. **PDF Implementation**: Add `pdf` and `printing` packages
3. **Testing**: Unit/widget tests for calculations
4. **Performance**: Pagination caching, lazy loading
5. **Navigation**: Add payroll link to dashboard menu
6. **Notifications**: Trigger FCM on new payslip release

## Production Readiness

- [x] Models and validation complete
- [x] Repository with error handling
- [x] UI screens fully implemented
- [x] State management setup
- [x] Routes configured
- [ ] PDF generation (ready for implementation)
- [ ] Share functionality (ready for implementation)
- [ ] Performance tested
- [ ] Security audit
- [ ] Compliance review (payroll data)
