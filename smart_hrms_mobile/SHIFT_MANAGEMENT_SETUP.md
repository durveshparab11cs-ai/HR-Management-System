# Shift Management Module - Setup & Integration Guide

## Overview
Complete shift management system for employees and managers with request/approval workflow.

**Status**: ✅ Complete (Phase 4 Task 4)

## Features Implemented

### 1. **Employee Shift Management**
- **MyShiftScreen** (`/shift`): Display current shift with time range
- **ShiftChangeRequestScreen** (`/shift/change-request`): Request shift change
- **ShiftHistoryScreen** (`/shift/history`): View past requests with status filtering

### 2. **Manager Approvals**
- **ShiftApprovalsScreen** (`/shift/approvals`): Manager approval interface
- Approve/Reject requests with remarks
- Status filtering (Pending/Approved/Rejected)

### 3. **Data Models**
- `Shift`: Shift definition with times and type (Morning/Afternoon/Evening/Night/Rotating)
- `EmployeeShift`: Current shift assignment
- `ShiftChangeRequest`: Change request with full lifecycle tracking

### 4. **API Integration**
```
GET    /api/v1/shifts/my-shift                     → Get current shift
GET    /api/v1/shifts/my-shift/available            → Available shifts for change
POST   /api/v1/shifts/request-change                → Submit change request
GET    /api/v1/shifts/history                       → Change request history (with pagination)
GET    /api/v1/shifts/approvals                     → Pending approvals for managers
POST   /api/v1/shifts/approvals/{id}/approve        → Approve request
POST   /api/v1/shifts/approvals/{id}/reject         → Reject request
POST   /api/v1/shifts/history/{id}/cancel           → Cancel pending request
```

## File Structure

```
lib/features/shift/
├── data/
│   ├── models/
│   │   └── shift_model.dart          # Shift, EmployeeShift, ShiftChangeRequest
│   └── repository/
│       └── shift_repository.dart     # API operations
├── presentation/
│   ├── providers/
│   │   └── shift_provider.dart       # Riverpod state management
│   └── screens/
│       ├── my_shift_screen.dart      # Current shift display
│       ├── shift_change_request_screen.dart  # Change form
│       ├── shift_history_screen.dart  # Employee history
│       └── shift_approvals_screen.dart # Manager approvals
└── __init__.dart
```

## Route Configuration

Added to `lib/core/router/app_router.dart`:
```dart
GoRoute(path: '/shift', name: 'shift-view', builder: (_) => const MyShiftScreen()),
GoRoute(path: '/shift/change-request', name: 'shift-change-request', builder: (_) => const ShiftChangeRequestScreen()),
GoRoute(path: '/shift/history', name: 'shift-history', builder: (_) => const ShiftHistoryScreen()),
GoRoute(path: '/shift/approvals', name: 'shift-approvals', builder: (_) => const ShiftApprovalsScreen()),
```

## State Management (Riverpod)

### Providers

**myShiftProvider**: Fetch current employee shift
```dart
final myShift = ref.watch(myShiftProvider);
```

**availableShiftsProvider**: Fetch available shifts for change requests
```dart
final shifts = ref.watch(availableShiftsProvider);
```

**shiftChangeHistoryProvider**: Paginated history with status filtering
```dart
final history = ref.watch(shiftChangeHistoryProvider({
  'page': 1,
  'perPage': 20,
  'status': 'pending', // optional
}));
```

**shiftChangeApprovalsProvider**: Manager approvals with filtering
```dart
final approvals = ref.watch(shiftChangeApprovalsProvider({
  'page': 1,
  'perPage': 20,
  'status': 'pending', // optional
}));
```

**shiftActionProvider**: Action state (loading/error/success)
- `requestShiftChange()`: Submit change request
- `approveShiftChange()`: Approve request (manager)
- `rejectShiftChange()`: Reject request (manager)
- `cancelShiftChangeRequest()`: Cancel pending request
- `clearMessages()`: Clear error/success messages

## UI/UX Features

### MyShiftScreen
- Large card display of current shift
- Time range visualization with login/logout icons
- Shift type badge
- Action buttons: "Request Shift Change" & "View Change Requests"
- Info card explaining shift system

### ShiftChangeRequestScreen
- Dropdown for available shifts
- Date picker for effective date (min 1 day ahead)
- Reason textarea with validation
- Disabled submit until all fields filled
- Success/error feedback

### ShiftHistoryScreen
- Status filter chips (All/Pending/Approved/Rejected)
- Status badge with color coding
- "Cancel Request" button for pending items
- Time ago display
- Remarks display for approved/rejected

### ShiftApprovalsScreen (Manager)
- Auto-filtered to "Pending" by default
- Employee avatar & info card
- Shift comparison (Current → Requested)
- Approve/Reject buttons with conditional dialog
- Remarks collection on rejection
- Status tracking

## Color Scheme

| Status | Color |
|--------|-------|
| Pending | Orange |
| Approved | Green (AppTheme.success) |
| Rejected | Red (AppTheme.error) |

## Testing Scenarios

### Employee Flow
1. Open "My Shift" → View current assignment
2. Click "Request Shift Change" → Submit with valid date/reason
3. View in "Change Requests" → Track approval status
4. Cancel if needed (pending only)

### Manager Flow
1. Open "Shift Change Approvals" → See pending requests
2. Review employee shift change request
3. Approve → Request updates immediately
4. Or Reject → Add remarks for employee feedback

### Edge Cases
- Date validation: Cannot select past dates or current date
- Field validation: All fields required before submission
- Status filtering: Proper pagination across filtered results
- Concurrent approvals: Multiple managers, single request

## Integration Checklist

- [x] Models created with JSON serialization
- [x] Repository with all CRUD operations
- [x] Riverpod providers & state notifier
- [x] All 4 screens implemented with Material Design 3
- [x] Routes added to app router
- [x] API constants already present
- [x] Error handling & validation
- [x] Pagination support
- [x] Status filtering
- [x] Role-based access (route-level gating optional)

## Backend API Requirements

### Request Format Examples

**Request Shift Change**
```json
POST /api/v1/shifts/request-change
{
  "requested_shift_id": 2,
  "requested_effective_from": "2024-08-15",
  "reason": "Family commitments"
}
```

**Approve Request**
```json
POST /api/v1/shifts/approvals/1/approve
{
  "remarks": "Approved for 2024-08-15"
}
```

**Reject Request**
```json
POST /api/v1/shifts/approvals/1/reject
{
  "remarks": "Cannot accommodate at this time"
}
```

## Next Steps

1. **Backend Integration**: Ensure Flask endpoints match API constants
2. **Testing**: Unit tests for repository, widget tests for screens
3. **Role-Gating**: Add role check for `/shift/approvals` (manager-only)
4. **Navigation**: Add shift links to dashboard/drawer for easy access
5. **Notifications**: Trigger FCM on approval/rejection
6. **Documentation**: Update user manual with shift workflow

## Known Limitations

- Manager approval workflow is single-level (no escalation)
- No shift swap direct feature (only change request)
- No future shift preview (only current)
- No bulk operations on requests

## Future Enhancements

- Shift swap with colleague (peer-to-peer)
- Shift calendar view with color coding
- Shift recommendations based on availability
- Shift history export/CSV
- Advanced filtering (by department, date range)
