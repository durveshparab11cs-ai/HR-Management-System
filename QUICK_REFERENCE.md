# Quick Reference: Your Excel Data Processing

## What Happens Automatically

### 📋 Your Excel Columns
```
Column A: EMP-CODE          → Employee code
Column B: NAME              → Employee name  
Column C: WORKING STATUS    → Status
Column D: WORKING LOCATION  → Hospital name (auto-matched)
Column E: full Shift timing → Shift hours (auto-parsed)
```

---

## 🔄 Automatic Processing Examples

### Example 1: Claim Team Employee
```
Excel Row:
├─ EMP-CODE: E-2406013
├─ NAME: Ajay Mahesh Kanjotkar
├─ WORKING STATUS: Active
├─ WORKING LOCATION: Claim Team ◄── AUTO-FETCHED
└─ full Shift timing: 10:00 AM to 7:00 PM ◄── AUTO-FETCHED

When employee registers with code E-2406013:
├─ ✓ System finds: "Claim Team" in master data
├─ ✓ Matches to: "Claim Department" hospital
├─ ✓ Sets GPS: 19.014847, 72.8452
├─ ✓ Parses shift: 10:00 AM - 7:00 PM
└─ ✓ Creates profile with all details

Check-in GPS validation:
└─ Must be within 100m of 19.014847, 72.8452 ✓
```

### Example 2: AIIMS Hospital Employee
```
Excel Row:
├─ EMP-CODE: E-2603028
├─ NAME: Aastha Vishwakarma
├─ WORKING STATUS: Active
├─ WORKING LOCATION: AIIMS Hospital (Gorakhpur) ◄── AUTO-FETCHED
└─ full Shift timing: 8:00 AM to 5:00 PM ◄── AUTO-FETCHED

When employee registers with code E-2603028:
├─ ✓ System finds: "AIIMS Hospital (Gorakhpur)"
├─ ✓ Matches to: AIIMS Hospital with its GPS
├─ ✓ Sets GPS: (AIIMS coordinates)
├─ ✓ Parses shift: 8:00 AM - 5:00 PM
└─ ✓ Creates profile with all details

Check-in GPS validation:
└─ Must be within radius of AIIMS coordinates ✓
```

---

## 📊 Location Mapping

### From Your Excel

| Working Location (Column D) | Maps To Hospital | GPS Coordinates |
|----------------------------|------------------|-----------------|
| **Claim Team** | Claim Department | 19.014847, 72.8452 |
| **AIIMS Hospital (Gorakhpur)** | AIIMS Hospital (Gorakhpur) | (AIIMS GPS) |
| **Amravati Hospital** | Amravati Hospital | (Amravati GPS) |
| **Bharatratra Di.dabaSaheb Ambedkar Hospital** | Bharatratra Hospital | (Hospital GPS) |
| **Akurdi Hospital** | Akurdi Hospital | (Hospital GPS) |

---

## ⏰ Shift Timing Mapping

### From Your Excel

| full Shift timing (Column E) | Start | End | Shift Type |
|------------------------------|-------|-----|------------|
| **8:00 AM to 5:00 PM** | 08:00 | 17:00 | Morning Shift |
| **9:00 AM to 6:00 PM** | 09:00 | 18:00 | Morning Shift |
| **10:00 AM to 7:00 PM** | 10:00 | 19:00 | Afternoon Shift |
| **11:00 AM to 8:00 PM** | 11:00 | 20:00 | Afternoon Shift |
| **12:00 PM to 9:00 PM** | 12:00 | 21:00 | Afternoon Shift |

---

## ✅ What's Automatic

### During Import (Admin)
1. Admin uploads your Excel
2. System reads columns A, B, C, D, E
3. Stores in employee_master:
   - ✓ employee_code
   - ✓ employee_name
   - ✓ working_status
   - ✓ working_location ← Stored!
   - ✓ shift_timing ← Stored!

### During Registration (Employee)
1. Employee enters: E-2406013
2. System fetches from master:
   - ✓ working_location: "Claim Team"
   - ✓ shift_timing: "10:00 AM to 7:00 PM"
3. System processes:
   - ✓ Finds hospital: "Claim Department"
   - ✓ Gets GPS: 19.014847, 72.8452
   - ✓ Parses shift: 10:00-19:00
4. Creates employee profile:
   - ✓ hospital_id: [Claim Dept ID]
   - ✓ current_shift: "Afternoon Shift"
   - ✓ shift_start_time: "10:00"
   - ✓ shift_end_time: "19:00"
   - ✓ is_flexible_shift: 0

### During Attendance (Employee)
1. Employee checks in
2. System uses employee's hospital GPS:
   - ✓ Reference: 19.014847, 72.8452
   - ✓ Radius: 100m
3. Validates and records:
   - ✓ GPS within range
   - ✓ Late if after 10:00 AM
   - ✓ Attendance recorded

---

## 🎯 Key Points

### ✅ Location (Column D) is AUTO-FETCHED
- During registration, system reads from master data
- Matches to hospital in database
- Sets GPS coordinates automatically
- Used for attendance validation

### ✅ Shift Time (Column E) is AUTO-FETCHED
- During registration, system reads from master data
- Parses start and end times
- Determines shift type (Morning/Afternoon/Evening/Night)
- Used for late marking and attendance rules

### ✅ No Manual Entry Needed
- Employee just enters: Code + Password
- System does everything else automatically
- All data from your Excel

---

## 🚀 Deployment Checklist

Before employees can register:

1. ☐ **Import Hospitals**
   - Create "Claim Department" with GPS: 19.014847, 72.8452
   - Create "AIIMS Hospital (Gorakhpur)" with its GPS
   - Create other hospitals from your Excel

2. ☐ **Import Employee Master**
   - Upload your Excel file (with columns A, B, C, D, E)
   - System stores working_location and shift_timing

3. ☐ **Test Registration**
   - Try registering with E-2406013
   - Should see: "Allocated to Claim Department. Afternoon Shift assigned."

4. ☐ **Test Attendance**
   - Check-in near Claim Department (19.014847, 72.8452)
   - Should validate GPS against hospital coordinates ✓

---

## 📞 Support

If hospital doesn't match:
- Check hospital name in database vs Excel
- Fuzzy matching uses 60% similarity threshold
- Add hospital manually if needed

If shift doesn't parse:
- Check format: "HH:MM AM to HH:MM PM"
- System supports flexible shifts too
- Logs show parsing results

---

**Everything is ready!** Just import your Excel and let employees register. 🎉
