# Module 2: Dashboard Implementation Plan

**Module:** Dashboard Complete  
**Status:** In Planning & Implementation  
**Priority:** High (Core user experience)  
**Estimated Duration:** 2-3 days  

---

## Overview

Module 2 enhances the dashboard with:
1. **Master Information Panel** - Employee profile snapshot with master data
2. **6-Month Attendance Chart** - Visual attendance trends (bar/line chart)

The dashboard currently shows basic attendance and leave info. We'll add a professional master data panel and expand the chart to show 6 months of data instead of just 7 days.

---

## Current State Analysis

### ✅ Already Implemented
- Attendance status card (check-in/out)
- Leave balance cards
- Quick actions buttons
- Basic 7-day attendance chart
- Refresh functionality
- Role-based summary cards (admin/manager)

### ❌ Missing / Needs Enhancement
1. Master information panel (employee details)
2. 6-month attendance chart (currently 7 days)
3. Enhanced styling/polish
4. Master data display (department, designation, branch, etc.)

---

## Architecture

### Data Flow
```
API (/dashboard) 
  ↓
DashboardRepository
  ↓
DashboardProvider (Riverpod)
  ↓
HomeScreen (Main Widget)
  ↓
├─ MasterInfoPanel (NEW)
├─ AttendanceCard (existing)
├─ QuickActions (existing)
├─ LeaveBalanceCard (existing)
└─ AttendanceChartWidget (enhanced)
```

### API Endpoints Used
1. `GET /dashboard` - Complete dashboard data (1 request)
2. `GET /dashboard/chart?days=180` - 6-month attendance data

---

## Implementation Plan

### Phase 1: Data Structures & Models

#### 1.1 Enhance DashboardModel
Create comprehensive `EmployeeInfo` model with:
- Employee code
- Full name
- Department
- Designation
- Branch
- Shift name
- Date of joining
- Reporting manager
- Email
- Phone

#### 1.2 Extend AttendanceChartData
- Support 180-day history
- Aggregate daily data into months

---

### Phase 2: UI Components

#### 2.1 Create MasterInfoPanel Widget
**Location:** `lib/features/dashboard/presentation/widgets/master_info_panel.dart`

**Features:**
- Employee avatar/initials
- Employee code (highlighted)
- Full name
- Department badge
- Designation
- Branch (if applicable)
- Shift assignment
- Reporting manager link (optional)

**Design:**
- Clean card layout
- Color-coded badges for department/shift
- Compact grid for master data (2-3 columns)
- Professional appearance matching website

#### 2.2 Enhance AttendanceChartWidget
**Location:** Modify existing `lib/features/dashboard/presentation/widgets/attendance_chart_widget.dart`

**Enhancements:**
- Switch from 7-day to 6-month view
- Add month/year labels on X-axis
- Show aggregated monthly data
- Interactive legend (show/hide series)
- Responsive sizing

**Chart Types:**
- Option 1: Bar chart (months as bars)
- Option 2: Line chart (trend line)
- Option 3: Combination (both)

---

### Phase 3: Dashboard Layout

#### 3.1 Update HomeScreen
**Layout:**
```
AppBar (existing)
  ↓
RefreshIndicator
  ↓
SingleChildScrollView
  ├─ MasterInfoPanel          [NEW - Top]
  ├─ AttendanceCard           [existing]
  ├─ QuickActions             [existing]
  ├─ SummaryCards             [existing if admin/manager]
  ├─ LeaveBalanceCard         [existing]
  ├─ AttendanceChart (6mo)    [ENHANCED]
  └─ [Future: More widgets]
```

---

## API Integration

### GET /dashboard - Complete Dashboard Data

**Request:**
```
GET https://hr-management-system-muqz.onrender.com/api/v1/dashboard
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "employee": {
      "employee_code": "E-2510016",
      "full_name": "Durvesh Parab",
      "first_name": "Durvesh",
      "last_name": "Parab",
      "department": "IT",
      "designation": "Software Engineer",
      "branch": "Main Office",
      "shift_name": "General",
      "date_of_joining": "2024-01-15",
      "reporting_manager": "Tejas Ashok Jadhav",
      "email": "durvesh@company.com",
      "phone": "+91-9876543210"
    },
    "today": {
      "date": "2026-07-28",
      "day_name": "Tuesday"
    },
    "attendance": {
      "today": {
        "status": "present",
        "check_in_time": "09:12",
        "check_out_time": null,
        "is_late": true,
        "late_minutes": 12
      },
      "can_check_in": false,
      "can_check_out": true,
      "office": {
        "name": "Main Office",
        "radius_metres": 200,
        "latitude": 19.076,
        "longitude": 72.877
      }
    },
    "leave": {
      "balances": [
        {
          "leave_type": "Paid Leave",
          "allowed": 6,
          "taken": 2,
          "available": 4
        }
      ],
      "pending_requests": 1
    },
    "quick_actions": [
      {
        "id": "check_out",
        "label": "Check Out",
        "icon": "logout",
        "color": "warning"
      }
    ]
  }
}
```

### GET /dashboard/chart - 6-Month Attendance Data

**Request:**
```
GET https://hr-management-system-muqz.onrender.com/api/v1/dashboard/chart?days=180
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "labels": ["Feb '26", "Mar '26", "Apr '26", "May '26", "Jun '26", "Jul '26"],
    "datasets": {
      "present": [22, 20, 23, 21, 22, 15],
      "absent": [1, 0, 0, 1, 0, 0],
      "on_leave": [0, 2, 0, 0, 1, 2]
    }
  }
}
```

---

## File Structure

```
lib/features/dashboard/
├── data/
│   ├── models/
│   │   ├── dashboard_model.dart       (enhance)
│   │   └── employee_info_model.dart   (NEW)
│   └── repository/
│       └── dashboard_repository.dart   (enhance)
├── presentation/
│   ├── providers/
│   │   └── dashboard_provider.dart    (enhance)
│   ├── screens/
│   │   └── home_screen.dart           (enhance)
│   └── widgets/
│       ├── master_info_panel.dart     (NEW)
│       ├── attendance_card.dart       (existing)
│       ├── attendance_chart_widget.dart (enhance)
│       ├── leave_balance_card.dart    (existing)
│       ├── quick_actions.dart         (existing)
│       └── summary_cards.dart         (existing)
```

---

## Design Requirements

### Master Info Panel
- **Size:** Full width card at top of dashboard
- **Spacing:** 16px padding
- **Content:** Grid layout (2-3 columns for info)
- **Colors:** 
  - Primary color for highlights
  - Badge colors for department/shift
  - Secondary text for labels
- **Typography:**
  - Employee code: 18px, bold, primary color
  - Full name: 24px, bold, primary text
  - Other fields: 12-14px, secondary text
- **Icons:** Department, designation, branch, shift icons

### 6-Month Attendance Chart
- **Height:** 250-300px
- **Padding:** 16px
- **Chart Type:** Bar or line chart
- **Colors:**
  - Present: Green (#66BB6A)
  - Absent: Red (#EF5350)
  - On Leave: Orange (#FF9800)
- **Legend:** Interactive (tap to show/hide series)
- **X-axis:** Month labels (Feb, Mar, Apr, etc.)
- **Y-axis:** Count (0-31)
- **Responsive:** Adapts to screen width

---

## Testing Requirements

### Unit Tests
1. Test EmployeeInfo model serialization/deserialization
2. Test enhanced AttendanceChartData with 180-day data
3. Test chart data aggregation logic

### Widget Tests
1. Test MasterInfoPanel rendering with sample data
2. Test 6-month chart display
3. Test responsive layout on different screen sizes

### Integration Tests
1. Test complete dashboard load flow
2. Test data refresh functionality
3. Test API error handling

---

## Success Criteria

✅ **Completion Requirements:**
1. Master info panel displays all employee data
2. 6-month attendance chart shows correct data
3. UI matches production website design
4. All APIs properly integrated
5. Error handling & loading states implemented
6. All tests passing (120+/116 minimum)
7. APK builds successfully
8. No build errors or warnings

---

## Modules Used

- **fl_chart:** 0.67.0 (for charts)
- **flutter_riverpod:** 2.6.1 (state management)
- **dio:** 5.x (API calls)
- **dartz:** 0.10.1 (Either/Result pattern)

---

## Implementation Order

1. ✅ Phase 1: Create models (EmployeeInfo, enhance dashboard models)
2. ✅ Phase 2: Update repository & providers
3. ✅ Phase 3: Create MasterInfoPanel widget
4. ✅ Phase 4: Enhance AttendanceChartWidget
5. ✅ Phase 5: Update HomeScreen layout
6. ✅ Phase 6: Add tests
7. ✅ Phase 7: Verify build & tests
8. ✅ Phase 8: Create completion report

---

## Dependencies

- ✅ fl_chart (already in pubspec.yaml)
- ✅ DioClient
- ✅ Riverpod
- ✅ App theme

---

## Timeline

- **Day 1:** Models + Repository + Widgets (MasterInfoPanel + Chart)
- **Day 2:** HomeScreen layout + Integration testing
- **Day 3:** Polish + Tests + Build verification

---

## Next: Module 3

After Dashboard completion:
- Attendance module
- Check-out flow
- Checkout selfie upload

---

**Status:** Ready to begin Phase 1 implementation
