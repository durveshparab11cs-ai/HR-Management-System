"""
admin/shift_import.py
==========================
Service for importing shift assignments from Excel.

Handles:
    - Reading Excel via openpyxl
    - Validating required columns (EMP-CODE, SHIFT NAME or SHIFT CODE)
    - Matching employees and shifts
    - Bulk shift assignment with detailed report
"""

import logging
from typing import Optional, Tuple, List, Dict

import openpyxl
from werkzeug.datastructures import FileStorage

from app.extensions.database import db
from app.models.employee import Employee
from app.models.company import Shift
from app.models.employee_shift_assignment import EmployeeShiftAssignment
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)


class ShiftImportService:

    REQUIRED_COLUMNS = {"EMP-CODE", "SHIFT"}
    # Note: Column names are case-insensitive and normalized during parsing
    # Accept multiple column name variations for shift input
    SHIFT_COLUMN_NAMES = {"SHIFT", "SHIFT NAME", "SHIFT TIMING", "SHIFT CODE"}

    def preview(self, file: FileStorage) -> dict:
        """
        Read Excel and return preview data without writing to DB.

        Returns:
            {
                success: bool,
                message: str,
                headers: list,
                rows: list of dicts,   # max 10 rows for preview
                total_rows: int,
                errors: list of str,
            }
        """
        try:
            wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
            ws = wb.active
            headers, rows, errors = self._parse_sheet(ws)
            if errors:
                return {"success": False, "message": errors[0], "errors": errors}
            preview_rows = rows[:10]
            return {
                "success":    True,
                "message":    f"{len(rows)} records found in Excel.",
                "headers":    headers,
                "rows":       preview_rows,
                "total_rows": len(rows),
                "errors":     [],
            }
        except Exception as exc:
            logger.error("Shift Excel preview failed: %s", exc)
            return {"success": False, "message": f"Could not read file: {exc}", "errors": [str(exc)]}

    def import_from_file(self, file: FileStorage, effective_date: Optional[str] = None, assigned_by_user_id: int = 1) -> dict:
        """
        Full import: read Excel, validate, deduplicate, assign shifts.

        Args:
            file: FileStorage object from form upload
            effective_date: Date string (YYYY-MM-DD) for shift assignments
            assigned_by_user_id: User ID who is assigning shifts

        Returns import summary:
            {
                success: bool,
                message: str,
                assigned:  int,    # successfully assigned
                skipped:   int,    # already assigned same shift
                notfound:  int,    # employee or shift not found
                errors:    int,    # validation/DB errors
                details:   list of {emp_code, emp_name, shift_name, status, reason}
            }
        """
        try:
            wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
            ws = wb.active
            headers, rows, errors = self._parse_sheet(ws)
            if errors:
                return {"success": False, "message": errors[0]}
        except Exception as exc:
            return {"success": False, "message": f"Could not read file: {exc}"}

        # Parse effective date
        if effective_date:
            try:
                eff_date = datetime.strptime(effective_date, '%Y-%m-%d').date()
            except ValueError:
                eff_date = date.today()
        else:
            eff_date = date.today()

        assigned   = 0
        skipped    = 0
        not_found  = 0
        error_count = 0
        details    = []

        for row in rows:
            emp_code = (row.get("EMP-CODE") or "").strip()  # Don't force uppercase
            shift_input = (row.get("SHIFT") or "").strip()

            if not emp_code or not shift_input:
                error_count += 1
                details.append({
                    "emp_code": emp_code or "?",
                    "emp_name": "?",
                    "shift_name": shift_input or "?",
                    "status": "error",
                    "reason": "Missing employee code or shift"
                })
                continue

            # Find employee by code - try both exact and case-insensitive match
            employee = Employee.query.filter_by(employee_code=emp_code).first()
            
            # If not found, try case-insensitive match
            if not employee:
                employee = Employee.query.filter(
                    Employee.employee_code.ilike(emp_code)
                ).first()
            
            if not employee:
                not_found += 1
                details.append({
                    "emp_code": emp_code,
                    "emp_name": "?",
                    "shift_name": shift_input,
                    "status": "notfound",
                    "reason": f"Employee code '{emp_code}' not found in system"
                })
                logger.warning(f"Employee not found: {emp_code}")
                continue

            # Find shift - try multiple match strategies
            shift = self._match_shift(shift_input)
            if not shift:
                not_found += 1
                details.append({
                    "emp_code": emp_code,
                    "emp_name": employee.name,
                    "shift_name": shift_input,
                    "status": "notfound",
                    "reason": f"Shift '{shift_input}' not found. Use exact name or code from dropdown."
                })
                continue

            # Assign shift
            try:
                # Check if employee already has this shift
                current_assignment = EmployeeShiftAssignment.query.filter(
                    EmployeeShiftAssignment.employee_id == employee.id,
                    EmployeeShiftAssignment.effective_until.is_(None)
                ).first()

                if current_assignment and current_assignment.shift_id == shift.id:
                    skipped += 1
                    details.append({
                        "emp_code": emp_code,
                        "emp_name": employee.name,
                        "shift_name": shift.name,
                        "status": "skipped",
                        "reason": "Already assigned to this shift"
                    })
                    continue

                # Close current assignment if exists and different
                if current_assignment:
                    current_assignment.effective_until = eff_date - timedelta(days=1)
                    db.session.add(current_assignment)

                # Create new assignment
                new_assignment = EmployeeShiftAssignment(
                    employee_id=employee.id,
                    shift_id=shift.id,
                    effective_from=eff_date,
                    assigned_by=assigned_by_user_id,
                    assigned_date=datetime.utcnow(),
                    reason="Bulk import from Excel",
                    remarks=f"Imported shift: {shift.name}"
                )
                db.session.add(new_assignment)
                assigned += 1
                details.append({
                    "emp_code": emp_code,
                    "emp_name": employee.name,
                    "shift_name": shift.name,
                    "status": "assigned",
                    "reason": ""
                })

            except Exception as exc:
                error_count += 1
                logger.error(f"Error assigning shift to {emp_code}: {str(exc)}")
                details.append({
                    "emp_code": emp_code,
                    "emp_name": employee.name,
                    "shift_name": shift_input,
                    "status": "error",
                    "reason": str(exc)
                })

        # Commit all changes
        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            logger.error(f"Shift import commit failed: {str(exc)}")
            return {
                "success": False,
                "message": f"Database error: {exc}"
            }

        logger.info("SHIFT_IMPORT | assigned=%s | skipped=%s | not_found=%s | errors=%s",
                    assigned, skipped, not_found, error_count)

        return {
            "success":    True,
            "message":    f"✅ Import complete. {assigned} assigned, {skipped} skipped, {not_found} not found, {error_count} errors.",
            "assigned":   assigned,
            "skipped":    skipped,
            "notfound":   not_found,
            "errors":     error_count,
            "total":      len(rows),
            "details":    details,
        }

    def _match_shift(self, shift_input: str) -> Optional:
        """
        Match shift input to database shift.

        Strategies:
        1. Exact match by name (case-insensitive)
        2. Exact match by code (case-insensitive)
        3. Partial match by name (first match)
        4. Search by time range (e.g., "11:00 AM to 08:00 PM")
        """
        if not shift_input:
            return None

        shift_input = shift_input.strip().upper()

        # Strategy 1: Exact match by name (case-insensitive)
        shift = Shift.query.filter(
            Shift.name.ilike(shift_input),
            Shift.is_active == True,
            Shift.is_deleted == False
        ).first()
        if shift:
            return shift

        # Strategy 2: Exact match by code (case-insensitive)
        shift = Shift.query.filter(
            Shift.code.ilike(shift_input),
            Shift.is_active == True,
            Shift.is_deleted == False
        ).first()
        if shift:
            return shift

        # Strategy 3: Partial match by name (contains)
        shift = Shift.query.filter(
            Shift.name.ilike(f"%{shift_input}%"),
            Shift.is_active == True,
            Shift.is_deleted == False
        ).first()
        if shift:
            return shift

        # Strategy 4: Try to match time range pattern (e.g., "11:00 AM to 08:00 PM")
        shift = self._match_by_time_range(shift_input)
        if shift:
            return shift

        return None

    def _match_by_time_range(self, shift_input: str) -> Optional:
        """
        Try to match shift by time range pattern.
        E.g., "11:00 AM to 08:00 PM" → find shift with matching start/end times
        """
        try:
            # Try to parse format: "HH:MM AM to HH:MM PM"
            import re
            match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)\s*to\s*(\d{1,2}):(\d{2})\s*(AM|PM)', shift_input, re.IGNORECASE)
            if not match:
                return None

            start_h, start_m, start_period, end_h, end_m, end_period = match.groups()
            
            # Convert to 24-hour format
            start_h, start_m = int(start_h), int(start_m)
            end_h, end_m = int(end_h), int(end_m)

            if start_period.upper() == 'PM' and start_h != 12:
                start_h += 12
            elif start_period.upper() == 'AM' and start_h == 12:
                start_h = 0

            if end_period.upper() == 'PM' and end_h != 12:
                end_h += 12
            elif end_period.upper() == 'AM' and end_h == 12:
                end_h = 0

            # Query for shift with matching times
            from datetime import time as dt_time
            start_time = dt_time(start_h, start_m)
            end_time = dt_time(end_h, end_m)

            shift = Shift.query.filter(
                Shift.start_time == start_time,
                Shift.end_time == end_time,
                Shift.is_active == True,
                Shift.is_deleted == False
            ).first()
            return shift

        except Exception as e:
            logger.debug(f"Time range matching failed for '{shift_input}': {e}")
            return None

    def _parse_sheet(self, ws) -> Tuple[List[str], List[Dict], List[str]]:
        """
        Extract headers and data rows from worksheet.

        Returns (headers, rows, errors).
        """
        rows_iter = iter(ws.rows)
        try:
            header_row = next(rows_iter)
        except StopIteration:
            return [], [], ["Excel file appears to be empty."]

        headers = [
            str(cell.value).strip().upper() if cell.value else ""
            for cell in header_row
        ]

        # Check required columns
        if "EMP-CODE" not in headers:
            return [], [], ["Missing required column: EMP-CODE. Found: " + ", ".join(headers[:10])]

        # Check for shift column (accept multiple names)
        shift_col_found = False
        shift_col_name = None
        for col_name in self.SHIFT_COLUMN_NAMES:
            if col_name in headers:
                shift_col_found = True
                shift_col_name = col_name
                break

        if not shift_col_found:
            return [], [], [
                f"Missing required column: SHIFT (or SHIFT NAME, SHIFT TIMING, SHIFT CODE). Found: {', '.join(headers[:10])}"
            ]

        emp_code_idx = headers.index("EMP-CODE")
        shift_idx = headers.index(shift_col_name)

        rows = []
        for sheet_row in rows_iter:
            vals = [cell.value for cell in sheet_row]
            if not any(vals):
                continue

            emp_code = str(vals[emp_code_idx]).strip() if len(vals) > emp_code_idx and vals[emp_code_idx] else ""
            shift_input = str(vals[shift_idx]).strip() if len(vals) > shift_idx and vals[shift_idx] else ""

            if emp_code and emp_code.lower() not in ("none", "nan", "emp-code"):
                row_data = {
                    "EMP-CODE": emp_code,
                    "SHIFT": shift_input
                }
                rows.append(row_data)

        return headers, rows, []
