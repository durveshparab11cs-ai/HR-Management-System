# How to Test the Attendance Status Fix

## Quick Testing Steps

### Test 1: PENDING Status (Before Photos Uploaded)
1. Go to Admin Dashboard
2. Find an employee who has checked in but hasn't uploaded both photos
3. Verify status shows as **plain text "Pending"** (gray, no background)
4. Expected: Light gray text without any colored badge

### Test 2: ABSENT Status (< 5 Hours Work)
1. Find an employee who:
   - Has uploaded BOTH check-in AND check-out photos
   - Worked LESS than 5 hours (e.g., 3 hours, 2 hours)
2. Verify status shows as **"Absent"** in RED background (`#dc3545`)
3. Expected: Red badge with white text

### Test 3: HALF_DAY Status (5-8:59 Hours Work)
1. Find an employee who:
   - Has uploaded BOTH check-in AND check-out photos
   - Worked between 5-8:59 hours (e.g., 6 hours, 7.5 hours)
2. Verify status shows as **"Half Day"** in YELLOW background (`#ffc107`)
3. Expected: Yellow badge with dark text

### Test 4: PRESENT Status (≥ 9 Hours Work)
1. Find an employee who:
   - Has uploaded BOTH check-in AND check-out photos
   - Worked 9+ hours (e.g., 9 hours, 10 hours, 12 hours)
2. Verify status shows as **"Present"** in GREEN background (`#28a745`)
3. Expected: Green badge with white text

## Where to View Status
1. **Admin Dashboard** (`/admin/`) → "Today's Attendance" table → Status column
2. **View All Attendance** (`/admin/attendance/all/`) → Status column → More detailed view

## Database Verification
If you want to verify the data directly:

```sql
-- Check attendance with photos
SELECT 
    a.id,
    a.employee_id,
    a.date,
    a.check_in_time,
    a.check_out_time,
    a.working_minutes,
    CASE 
        WHEN a.working_minutes < 300 THEN 'absent'
        WHEN a.working_minutes < 540 THEN 'half_day'
        ELSE 'present'
    END as expected_status,
    ap.image_data,
    ap.checkout_image_data
FROM attendance a
LEFT JOIN attendance_photos ap ON a.id = ap.attendance_id
WHERE a.date = CURRENT_DATE
ORDER BY a.check_in_time DESC;
```

## Common Issues & Solutions

### Issue: Still showing PRESENT for employees with < 5 hours
**Solution**: Check that both `image_data` AND `checkout_image_data` exist in the `attendance_photos` table

### Issue: Status showing as "PENDING" when should be ABSENT
**Solution**: Verify both photos have been uploaded by checking the photo modal on the attendance detail view

### Issue: Working hours calculated wrong
**Solution**: Check that check-in and check-out times are being recorded correctly (should be UTC in database)

## API Testing (For Backend Verification)
```bash
# Get today's attendance with status
curl -X GET "http://localhost:5000/api/v1/attendance/today" \
  -H "Authorization: Bearer <token>"

# Expected response includes status field:
# "status": "pending" | "absent" | "half_day" | "present"
```

## Color Code Reference
| Status | Hex Color | RGB Color | Background? |
|--------|-----------|-----------|-------------|
| PENDING | — | Gray #6c757d | No (plain text) |
| ABSENT | #dc3545 | Red | Yes |
| HALF_DAY | #ffc107 | Yellow | Yes |
| PRESENT | #28a745 | Green | Yes |

## Notes
- Status is computed in real-time when viewing the dashboard (not stored in DB)
- Working hours are calculated as: `(check_out_time - check_in_time) in minutes`
- Thresholds:
  - ABSENT: < 300 minutes (< 5 hours)
  - HALF_DAY: 300-539 minutes (5-8:59 hours)
  - PRESENT: ≥ 540 minutes (≥ 9 hours)
- Photos must be uploaded AFTER check-out to trigger status calculation
- If either check-in OR check-out photo is missing, status remains PENDING
