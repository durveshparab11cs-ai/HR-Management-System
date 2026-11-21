# SMART HRMS — DATA REQUESTS CATALOG
**CS Creative Solutions | Required Real Datasets & Excel Templates**
*Document Version: 1.0.0 | Date: 2026-11-21*

> **NON-NEGOTIABLE POLICY**: No dummy data, placeholder numbers, sample names, or guessed policy values will ever be created or assumed by the system.
> Every parameter below must be supplied by CS Creative Solutions. Below is the comprehensive list of real data needed, grouped by operational module with exact column layouts for Excel/CSV import templates.

---

## Summary of Data Groups

| Group | Module | Status | Deliverable Format |
| :--- | :--- | :--- | :--- |
| **Group 1** | Company Profile & Legal Identity | Pending | Configuration Form / Document |
| **Group 2** | Organization Structure | Pending | Excel / CSV (`departments.xlsx`) |
| **Group 3** | Employee Master & Full Profiles | In Progress (541 codes provided) | Excel / CSV (`employees_full.xlsx`) |
| **Group 4** | Hospitals & Geo-Fencing Locations | Partial (46 names provided) | Excel / CSV (`hospitals_geofence.xlsx`) |
| **Group 5** | Shifts & Work Timing Rules | Pending verification | Excel / CSV (`shifts_policy.xlsx`) |
| **Group 6** | Company Holidays Calendar | Pending verification | Excel / CSV (`holidays_2026.xlsx`) |
| **Group 7** | Leave & Comp-Off Policies | Pending | Configuration Form / Policy Sheet |
| **Group 8** | Attendance & Overtime Rules | Pending | Configuration Form / Policy Sheet |
| **Group 9** | Statutory Labour & Tax Rates | Pending | Configuration Form / Slabs Sheet |
| **Group 10** | Salary Structures & Compensation | Pending | Excel / CSV (`salary_structures.xlsx`) |
| **Group 11** | Opening Balances (Leaves & Comp-Off) | Pending | Excel / CSV (`opening_balances.xlsx`) |
| **Group 12** | Kiosk Hardware & Office Devices | Pending | Device Tokens / MAC IDs / IPs |
| **Group 13** | Recruitment Content & Jobs | Pending | Active Requisitions / Job Profiles |
| **Group 14** | Branding Assets & Signatures | Pending | High-Resolution Images (PNG/SVG) |

---

## Detailed Specifications by Module

### Group 1: Company Profile & Legal Identity
*Needed for official payslips, compliance registers, PF/ESI filing formats, and system headers.*

| Field Name | Type | Mandatory? | Notes / Format |
| :--- | :--- | :--- | :--- |
| **Company Legal Name** | String | Yes | E.g., `CS Creative Solutions Private Limited` |
| **Trading / Brand Name** | String | Yes | E.g., `CS Creative Solutions` |
| **Registered Address** | Text | Yes | Complete physical address with City, State, PIN code |
| **Corporate Office Address** | Text | Yes | If different from registered address |
| **Company PAN** | String(10) | Yes | Format: `AAAAA9999A` |
| **Company TAN** | String(10) | Yes | Format: `AAAA99999A` |
| **GSTIN** | String(15) | Yes | Format: `27AAAAA9999A1Z5` (Maharashtra or respective state) |
| **EPFO Establishment Code** | String(25) | Yes | E.g., `MH/BAN/0000000/000` |
| **ESIC Employer Code** | String(17) | Yes | 17-digit numeric code |
| **Professional Tax Registration (PTRC/PTEC)** | String(30) | Yes | State-specific PT registration numbers |
| **Labour Identification Number (LIN)** | String(20) | Optional | MoLE LIN identifier |
| **Primary Contact Email & Phone** | String | Yes | HR/Payroll official email and contact number |

---

### Group 2: Organization Structure
*File: `departments.xlsx` & `designations.xlsx`*

#### Departments Import Layout
| Column Header | Data Type | Mandatory? | Description & Allowed Values |
| :--- | :--- | :--- | :--- |
| `department_code` | String(20) | Yes | Unique identifier (e.g., `DEPT-OPS`, `DEPT-HR`, `DEPT-MED`) |
| `department_name` | String(100) | Yes | Official department name |
| `head_employee_code` | String(30) | Optional | Employee Code of Department Head (e.g., `E-2512012`) |
| `is_active` | Boolean | Yes | `TRUE` or `FALSE` |

#### Designations Import Layout
| Column Header | Data Type | Mandatory? | Description & Allowed Values |
| :--- | :--- | :--- | :--- |
| `designation_code` | String(20) | Yes | Unique identifier (e.g., `DES-COOR`, `DES-NURSE`, `DES-EXE`) |
| `designation_title` | String(100) | Yes | Official title |
| `department_code` | String(20) | Yes | Foreign key to valid `department_code` |
| `grade_level` | String(20) | Optional | Internal grade/band (e.g., `L1`, `L2`, `Senior`, `Executive`) |
| `is_active` | Boolean | Yes | `TRUE` or `FALSE` |

---

### Group 3: Employee Master & Extended Profiles
*File: `employees_full.xlsx`*
*Note: The user provided 541 employee codes and full names in `data/real_employee_master_541.csv`. The fields below complete the master profile for HR compliance and payroll.*

| Column Header | Data Type | Mandatory? | Format & Validation Notes |
| :--- | :--- | :--- | :--- |
| `employee_code` | String(30) | Yes | Primary Key. E.g., `E-2606026`, `I-2606001` |
| `first_name` | String(60) | Yes | Employee's given name |
| `last_name` | String(60) | Yes | Employee's surname |
| `gender` | String(10) | Yes | `Male`, `Female`, `Other` |
| `date_of_birth` | Date | Yes | `YYYY-MM-DD` |
| `date_of_joining` | Date | Yes | `YYYY-MM-DD` |
| `department_code` | String(20) | Yes | Must match valid Department Code |
| `designation_code` | String(20) | Yes | Must match valid Designation Code |
| `working_location` | String(100) | Yes | Default hospital/office location (e.g., `Head Office`, `KEM Hospital`) |
| `reporting_manager_code` | String(30) | Optional | Employee Code of supervisor (for leave & shift approvals) |
| `work_email` | String(120) | Optional | Company email address |
| `personal_email` | String(120) | Yes | Personal email for password reset / payslip delivery |
| `mobile_number` | String(15) | Yes | 10-digit Indian mobile number (`9876543210`) |
| `emergency_contact_phone`| String(15) | Optional | Secondary contact number |
| `pan_number` | String(10) | Yes | Format: `AAAAA9999A` (encrypted in database) |
| `aadhaar_number` | String(12) | Optional | 12-digit UIDAI number (masked, encrypted) |
| `uan_number` | String(12) | Optional | 12-digit Universal Account Number for EPF |
| `esic_number` | String(17) | Optional | ESIC Insurance Number (if covered) |
| `bank_name` | String(100) | Yes | E.g., `HDFC Bank`, `State Bank of India` |
| `bank_account_number` | String(30) | Yes | Account number for direct salary transfer |
| `bank_ifsc_code` | String(11) | Yes | 11-character Indian Financial System Code |
| `employment_status` | String(20) | Yes | `Permanent`, `Probation`, `Contract`, `Intern` |

---

### Group 4: Hospitals & Geo-Fencing Locations
*File: `hospitals_geofence.xlsx`*
*Needed for location-based mobile check-in verification and out-of-boundary flags.*

| Column Header | Data Type | Mandatory? | Description & Format |
| :--- | :--- | :--- | :--- |
| `hospital_code` | String(20) | Yes | Unique ID (e.g., `HOSP-001`, `HOSP-KEM`) |
| `hospital_name` | String(150) | Yes | Full institutional name |
| `address` | Text | Yes | Physical street address and area |
| `city` | String(60) | Yes | E.g., `Mumbai`, `Pune`, `Thane` |
| `latitude` | Decimal(9,6)| Yes | E.g., `18.520430` (verified coordinates) |
| `longitude` | Decimal(9,6)| Yes | E.g., `73.856744` (verified coordinates) |
| `geofence_radius_meters` | Integer | Yes | Radius allowed for mobile punch (e.g., `150`, `300`, `500`) |
| `contact_person` | String(100) | Optional | Name of onsite coordinator / supervisor |
| `contact_phone` | String(15) | Optional | Contact number for onsite supervisor |
| `is_active` | Boolean | Yes | `TRUE` or `FALSE` |

---

### Group 5: Shifts & Work Timing Rules
*File: `shifts_policy.xlsx`*

| Column Header | Data Type | Mandatory? | Notes & Format |
| :--- | :--- | :--- | :--- |
| `shift_code` | String(20) | Yes | E.g., `M-01` (Morning), `G-01` (General), `N-01` (Night) |
| `shift_name` | String(60) | Yes | E.g., `General Day Shift`, `Night Shift 1` |
| `start_time` | Time | Yes | `HH:MM` in 24-hr format (e.g., `09:30`) |
| `end_time` | Time | Yes | `HH:MM` in 24-hr format (e.g., `18:30`) |
| `is_overnight` | Boolean | Yes | `TRUE` if shift ends on next calendar day |
| `grace_period_minutes` | Integer | Yes | Allowable late arrival without penalty (e.g., `15` mins) |
| `half_day_threshold_hours`| Decimal(3,1)| Yes | Min working hours for half-day credit (e.g., `4.5` hrs) |
| `full_day_threshold_hours`| Decimal(3,1)| Yes | Min working hours for full-day credit (e.g., `8.0` hrs) |
| `overtime_eligible` | Boolean | Yes | `TRUE` or `FALSE` |
| `overtime_min_minutes` | Integer | Optional | Min minutes worked past shift end to trigger OT |

---

### Group 6: Company Holidays Calendar
*File: `holidays_2026.xlsx`*

| Column Header | Data Type | Mandatory? | Notes & Format |
| :--- | :--- | :--- | :--- |
| `holiday_date` | Date | Yes | `YYYY-MM-DD` |
| `holiday_name` | String(100) | Yes | Official holiday name (e.g., `Republic Day`, `Independence Day`) |
| `holiday_type` | String(20) | Yes | `National`, `State`, `Festival`, `Optional` |
| `applies_to_locations` | String(200) | Yes | `All` or comma-separated list of hospital codes |
| `is_paid` | Boolean | Yes | `TRUE` or `FALSE` |

---

### Group 7: Leave & Comp-Off Policies

Please confirm the following policy rules (no defaults are assumed):
1. **Casual Leave (CL)**: Annual quota, monthly credit rate, whether unavailed lapses or carries forward.
2. **Sick Leave (SL)**: Annual quota, medical certificate requirement threshold (e.g., > 2 days).
3. **Privilege / Earned Leave (PL)**: Annual entitlement, accrual formula, max accumulation ceiling.
4. **Comp-Off Rules**:
   - Minimum hours required on Sunday/Holiday to earn 0.5 day credit: `[ ___ hours ]`
   - Minimum hours required on Sunday/Holiday to earn 1.0 day credit: `[ ___ hours ]`
   - Validity period: Set to 90 days / 3 months FIFO expiry.
   - Whether overtime payout is ever allowed in lieu of comp-off leave credit.
5. **Manager Escalation Window**: Number of business days after which a pending leave auto-escalates to Super Admin: `[ ___ days ]`

---

### Group 8: Attendance & Punch Policies

1. **Repeat Punch Buffer**: Seconds/minutes within which accidental double-punches are ignored: `[ ___ minutes ]` (default 2 min).
2. **Late Mark Penalty**: Number of late arrivals per calendar month before a half-day deduction occurs: `[ ___ marks ]`.
3. **Early Leave Policy**: Permitted early departures per month before deduction.
4. **Overnight Shift Attribution Cutoff**: Hour of day (e.g., `06:00` AM) used to bind overnight punches to shift-start date.
5. **Missing Punch Regularization**: Max days allowed for an employee to request attendance regularization: `[ ___ days ]`.

---

### Group 9: Statutory Labour Compliance & Tax Parameters
*Mandatory verification before Payroll can be activated.*

1. **Employees' Provident Fund (EPF)**:
   - Employee Contribution: `[ ___ % ]` (Standard: 12% of Basic + DA)
   - Employer Contribution: Breakdown between EPF (3.67%), EPS (8.33%), EDLI (0.5%), and Admin charges.
   - Wage Ceiling: Whether statutory ceiling of ₹15,000 applies or actual Basic pay is considered.
2. **Employee State Insurance (ESIC)**:
   - Monthly Gross Wage Ceiling: `[ ₹21,000 or specific amount ]`
   - Employee Rate: `[ ___ % ]` (Standard: 0.75%)
   - Employer Rate: `[ ___ % ]` (Standard: 3.25%)
3. **Professional Tax (PT)**:
   - Applicable State(s): E.g., Maharashtra (PT Act 1975) slab confirmation:
     - Gross ≤ ₹7,500 (Men/Women): ₹0
     - ₹7,501 to ₹10,000: ₹175/month
     - > ₹10,000: ₹200/month (₹300 in February)
4. **Labour Welfare Fund (LWF)**:
   - State-specific periodicity (Half-yearly in June & Dec for Maharashtra) and employee/employer share amounts.

---

### Group 10: Salary Structures & Compensation Slabs
*File: `salary_structures.xlsx`*

| Column Header | Data Type | Mandatory? | Notes & Format |
| :--- | :--- | :--- | :--- |
| `employee_code` | String(30) | Yes | Valid employee identifier |
| `effective_from` | Date | Yes | `YYYY-MM-DD` (date from which salary takes effect) |
| `monthly_ctc` | Decimal(12,2)| Yes | Total monthly Cost-to-Company in INR |
| `basic_salary` | Decimal(12,2)| Yes | Fixed Basic Pay |
| `hra` | Decimal(12,2)| Yes | House Rent Allowance |
| `special_allowance` | Decimal(12,2)| Yes | Balancing / Special Allowance |
| `conveyance_allowance`| Decimal(12,2)| Optional | Travel/Conveyance component |
| `medical_allowance` | Decimal(12,2)| Optional | Fixed Medical component |
| `other_allowances` | Decimal(12,2)| Optional | Performance or location allowance |
| `pf_applicable` | Boolean | Yes | `TRUE` if employee is enrolled in PF |
| `esi_applicable` | Boolean | Yes | `TRUE` if covered under ESIC |
| `pt_applicable` | Boolean | Yes | `TRUE` if subject to state Professional Tax |
| `tds_monthly_deduction`| Decimal(12,2)| Optional | Monthly income tax withholding amount |

---

### Group 11: Opening Balances (As of Migration Date)
*File: `opening_balances.xlsx`*

| Column Header | Data Type | Mandatory? | Notes & Format |
| :--- | :--- | :--- | :--- |
| `employee_code` | String(30) | Yes | Valid employee code |
| `as_of_date` | Date | Yes | `YYYY-MM-DD` (e.g., `2026-11-01`) |
| `cl_balance` | Decimal(4,1)| Yes | Available Casual Leave days |
| `sl_balance` | Decimal(4,1)| Yes | Available Sick Leave days |
| `pl_balance` | Decimal(4,1)| Yes | Available Privilege Leave days |
| `comp_off_balance` | Decimal(4,1)| Yes | Unexpired Comp-Off days |
| `comp_off_earliest_expiry`| Date | Optional | Expiry date of the oldest active comp-off credit |
| `ytd_gross_earnings` | Decimal(12,2)| Optional | Financial year-to-date gross for tax calculations |
| `ytd_pf_deducted` | Decimal(12,2)| Optional | Financial year-to-date PF deducted |
| `ytd_tax_deducted` | Decimal(12,2)| Optional | Financial year-to-date TDS paid |

---

### Group 12: Kiosk Hardware & Office Devices
*Needed to register and hardware-lock the two office attendance terminals.*

| Terminal Name | Location | Identifying Attribute | Required Value |
| :--- | :--- | :--- | :--- |
| **Kiosk Device 1** | Head Office Front Desk | Static IP / MAC Address / Device ID | `[ Provide IP/MAC ]` |
| **Kiosk Device 2** | Operations Room | Static IP / MAC Address / Device ID | `[ Provide IP/MAC ]` |

---

### Group 13: Recruitment Content & Active Requisitions
1. List of active job openings (Title, Department, Hospital Location, Min Experience, CTC Range, Job Description).
2. Hiring workflow stages (Default: Applied → Screened → Interview 1 → Interview 2 → Offer → Hired).
3. Standard CS Creative Solutions Offer Letter text template (with placeholder tokens for Salary, DOJ, Location).

---

### Group 14: Branding Assets & Official Signatures
*Needed for payslips, system favicon, splash screens, and offer letters.*

1. **Company Logo**: High-resolution PNG and SVG with transparent background (Full horizontal lockup and square app icon).
2. **Official Stamp / Seal**: High-resolution transparent PNG of CS Creative Solutions company seal.
3. **Authorized Signatory Image**: High-resolution transparent PNG of authorized signatory's signature for automated payslip stamping.
