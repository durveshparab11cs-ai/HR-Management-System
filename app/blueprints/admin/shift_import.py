"""
admin/shift_import.py
==========================
Service for importing shift AND hospital assignments from Excel.

Handles:
    - Reading Excel via openpyxl
    - Validating required columns (EMP-CODE, SHIFT, HOSPITAL NAME)
    - Matching employees, shifts, and hospitals
    - Bulk shift + hospital assignment with detailed report
"""

import logging
from typing import Optional, Tuple, List, Dict

import openpyxl
from werkzeug.datastructures import FileStorage

from app.extensions.database import db
from app.models.employee import Employee
from app.models.company import Shift
from app.models.hospital import Hospital
from app.models.employee_shift_assignment import EmployeeShiftAssignment
from app.models.hospital_assignment import EmployeeHospitalAssignment
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)


class ShiftImportService:

    REQUIRED_COLUMNS = {"EMP-CODE"}
    # Accept multiple column name variations for shift input
    SHIFT_COLUMN_NAMES = {"SHIFT", "SHIFT NAME", "SHIFT TIMING", "SHIFT CODE"}
    HOSPITAL_COLUMN_NAMES = {"HOSPITAL", "HOSPITAL NAME", "WORKING LOCATION"}

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
        Full import: read Excel, validate, assign shifts AND hospitals.

        Args:
            file: FileStorage object from form upload
            effective_date: Date string (YYYY-MM-DD) for assignments
            assigned_by_user_id: User ID who is assigning

        Returns import summary:
            {
                success: bool,
                message: str,
                assigned:  int,    # successfully assigned shifts
                hospitals_assigned: int,  # successfully assigned hospitals
                skipped:   int,    # already assigned
                notfound:  int,    # employee/shift/hospital not found
                errors:    int,    # validation/DB errors
                details:   list of {emp_code, emp_name, shift_name, hospital_name, status, reason}
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

        logger.info(f"[IMPORT_START] effective_date={eff_date}, file_name={file.filename}")
        logger.info(f"[IMPORT_START] Parsed sheet headers: {headers}")
        logger.info(f"[IMPORT_START] Total rows to process: {len(rows)}")

        assigned       = 0
        hospitals_assigned = 0
        skipped        = 0
        not_found      = 0
        error_count    = 0
        details        = []

        for row_num, row in enumerate(rows, start=1):
            emp_code = (row.get("EMP-CODE") or "").strip()
            shift_input = (row.get("SHIFT") or "").strip()
            hospital_input = (row.get("HOSPITAL") or "").strip()
            
            logger.info(f"[ROW_{row_num}] emp_code='{emp_code}', shift='{shift_input}', hospital='{hospital_input}'")

            if not emp_code:
                error_count += 1
                details.append({
                    "emp_code": emp_code or "?",
                    "emp_name": "?",
                    "shift_name": shift_input or "?",
                    "hospital_name": hospital_input or "?",
                    "status": "error",
                    "reason": "Missing employee code"
                })
                continue

            # Find employee by code (with case-insensitive fallback)
            employee = Employee.query.filter_by(employee_code=emp_code).first()
            
            if not employee:
                employee = Employee.query.filter(
                    Employee.employee_code.ilike(emp_code)
                ).first()
            
            # AUTO-CREATE EMPLOYEE IF NOT FOUND
            if not employee:
                try:
                    logger.info(f"[AUTO_CREATE_EMPLOYEE] Creating employee: {emp_code}")
                    
                    # Get or create a stub user for this employee
                    from app.models.user import User
                    from werkzeug.security import generate_password_hash
                    
                    user = User.query.filter_by(username=emp_code.lower()).first()
                    if not user:
                        # Split employee code to create name parts
                        parts = emp_code.split('-')
                        first_name = parts[0] if parts else "Employee"
                        last_name = emp_code
                        
                        user = User(
                            username=emp_code.lower(),
                            email=f"{emp_code.lower()}@company.local",
                            first_name=first_name,
                            last_name=last_name,
                            password_hash=generate_password_hash("temp_password"),
                            role='employee',
                            status='active'
                        )
                        db.session.add(user)
                        db.session.flush()
                    
                    # Create Employee record
                    employee = Employee(
                        user_id=user.id,
                        employee_code=emp_code,
                        department="General",
                        designation="Staff"
                    )
                    db.session.add(employee)
                    db.session.flush()
                    logger.info(f"[AUTO_CREATE_EMPLOYEE] Created employee: {emp_code} (user_id={user.id})")
                    
                except Exception as exc:
                    logger.error(f"[AUTO_CREATE_EMPLOYEE] Failed to create employee {emp_code}: {str(exc)}")
                    error_count += 1
                    details.append({
                        "emp_code": emp_code,
                        "emp_name": "?",
                        "shift_name": shift_input or "?",
                        "hospital_name": hospital_input or "?",
                        "status": "error",
                        "reason": f"Could not create employee: {str(exc)}"
                    })
                    continue
            
            if not employee:
                not_found += 1
                logger.warning(f"Employee not found and could not be created: {emp_code}")
                continue

            shift = None
            hospital_name = None

            # Find shift if provided
            if shift_input:
                shift = self._match_shift(shift_input)
                if not shift:
                    logger.warning(f"Shift not found: {shift_input}")
                    shift = None

            # Find hospital if provided
            if hospital_input:
                logger.info(f"[HOSPITAL_LOOKUP] Looking for: '{hospital_input}'")
                
                # Normalize hospital name for comparison
                hospital_normalized = hospital_input.strip()
                
                # Try exact match first (case-insensitive)
                hospital = Hospital.query.filter(
                    Hospital.hospital_name.ilike(hospital_normalized),
                    Hospital.is_active == True,
                    Hospital.is_deleted == False
                ).first()
                
                if hospital:
                    logger.info(f"[HOSPITAL_LOOKUP] Exact match: '{hospital.hospital_name}'")
                    hospital_name = hospital.hospital_name
                else:
                    # If exact match fails, try partial match (contains)
                    hospital = Hospital.query.filter(
                        Hospital.hospital_name.ilike(f"%{hospital_normalized}%"),
                        Hospital.is_active == True,
                        Hospital.is_deleted == False
                    ).first()
                    
                    if hospital:
                        logger.info(f"[HOSPITAL_LOOKUP] Partial match: '{hospital.hospital_name}'")
                        hospital_name = hospital.hospital_name
                    else:
                        # Try keyword matching
                        all_hospitals = Hospital.query.filter(
                            Hospital.is_active == True,
                            Hospital.is_deleted == False
                        ).all()
                        keywords = [k.strip().lower() for k in hospital_normalized.split() if k.strip()]
                        
                        for h in all_hospitals:
                            if all(kw in h.hospital_name.lower() for kw in keywords):
                                logger.info(f"[HOSPITAL_LOOKUP] Keyword match: '{h.hospital_name}'")
                                hospital_name = h.hospital_name
                                break
                        
                        if not hospital_name:
                            # Try special name mapping for known variations
                            name_mapping = {
                                'DR. RN COOPER HOSPITAL': 'Dr R.N. Cooper Muncipial General Hospital',
                                'RN COOPER': 'Dr R.N. Cooper Muncipial General Hospital',
                                'SHANTILAL SANGHAVI EYE HOSPITAL': 'Shantitol Shanghvi Eye Hospital',
                                'SHANTILAL SHANGHVI EYE HOSPITAL': 'Shantitol Shanghvi Eye Hospital',
                                'Shantilol Shanghvi Eye Hospital': 'Shantitol Shanghvi Eye Hospital',
                                'WALAWALKAR': 'Walawatkar Hospital',
                                'WALAWALKER': 'Walawatkar Hospital',
                                'WALAWATKAR': 'Walawatkar Hospital',
                            }
                            
                            normalized_input = hospital_normalized.upper()
                            for key, mapped_name in name_mapping.items():
                                if key.upper() in normalized_input or normalized_input in key.upper():
                                    hospital = Hospital.query.filter_by(hospital_name=mapped_name).first()
                                    if hospital:
                                        logger.info(f"[HOSPITAL_LOOKUP] Name mapping match: '{hospital.hospital_name}'")
                                        hospital_name = hospital.hospital_name
                                        break
                            
                            if not hospital_name:
                                logger.warning(f"[HOSPITAL_LOOKUP] No match for: '{hospital_input}'")
                                not_found += 1

            # Skip row only if BOTH shift AND hospital are missing/failed
            if (shift_input and not shift) and (hospital_input and not hospital_name):
                details.append({
                    "emp_code": emp_code,
                    "emp_name": employee.name,
                    "shift_name": shift_input or "—",
                    "hospital_name": hospital_input or "—",
                    "status": "notfound",
                    "reason": "Both shift and hospital not found"
                })
                continue

            # Skip if nothing to assign
            if not shift and not hospital_name:
                # DON'T count as error - just skip silently for not found employees
                logger.info(f"[SKIP] {emp_code}: No shift or hospital to assign")
                continue

            # Assign shift if provided
            if shift:
                try:
                    current_assignment = EmployeeShiftAssignment.query.filter(
                        EmployeeShiftAssignment.employee_id == employee.id,
                        EmployeeShiftAssignment.effective_until.is_(None)
                    ).first()

                    if current_assignment and current_assignment.shift_id == shift.id:
                        skipped += 1
                        logger.info(f"Shift already assigned: {emp_code}")
                    else:
                        # Close previous if different
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
                        logger.info(f"Shift assigned: {emp_code} → {shift.name}")

                except Exception as exc:
                    error_count += 1
                    logger.error(f"Error assigning shift to {emp_code}: {str(exc)}")

            # Assign hospital if provided
            if hospital_name:
                try:
                    logger.info(f"[HOSPITAL_ASSIGN_START] emp_id={employee.id}, hospital='{hospital_name}'")
                    
                    # CRITICAL: Verify the table exists and is accessible
                    from sqlalchemy import inspect as sa_inspect
                    insp = sa_inspect(db.engine)
                    tables = insp.get_table_names()
                    if 'employee_hospital_assignments' not in tables:
                        logger.error(f"[HOSPITAL_ASSIGN] FATAL: employee_hospital_assignments table does not exist!")
                        logger.error(f"[HOSPITAL_ASSIGN] Available tables: {tables}")
                        error_count += 1
                        continue
                    
                    current_hospital = EmployeeHospitalAssignment.query.filter(
                        EmployeeHospitalAssignment.employee_id == employee.id,
                        EmployeeHospitalAssignment.effective_until.is_(None)
                    ).first()
                    
                    logger.info(f"[HOSPITAL_ASSIGN] Current hospital: {current_hospital}")

                    if current_hospital and current_hospital.hospital_name == hospital_name:
                        skipped += 1
                        logger.info(f"[HOSPITAL_ASSIGN] Skipping - already assigned to same hospital")
                    else:
                        logger.info(f"[HOSPITAL_ASSIGN] Will create new assignment")
                        
                        # Close previous if different
                        if current_hospital:
                            current_hospital.effective_until = eff_date - timedelta(days=1)
                            db.session.add(current_hospital)
                            logger.info(f"[HOSPITAL_ASSIGN] Marked previous for update")

                        # Create new assignment
                        logger.info(f"[HOSPITAL_ASSIGN] Creating EmployeeHospitalAssignment object...")
                        new_hospital_assignment = EmployeeHospitalAssignment(
                            employee_id=employee.id,
                            hospital_name=hospital_name,
                            effective_from=eff_date,
                            notes=f"Bulk import by user {assigned_by_user_id}"
                        )
                        logger.info(f"[HOSPITAL_ASSIGN] Created object: {new_hospital_assignment}")
                        logger.info(f"[HOSPITAL_ASSIGN] Object attributes: id={new_hospital_assignment.id}, emp_id={new_hospital_assignment.employee_id}, hospital='{new_hospital_assignment.hospital_name}', effective_from={new_hospital_assignment.effective_from}")
                        
                        db.session.add(new_hospital_assignment)
                        logger.info(f"[HOSPITAL_ASSIGN] Added to session")
                        
                        # Verify object was added
                        in_session = new_hospital_assignment in db.session.new
                        logger.info(f"[HOSPITAL_ASSIGN] In session.new: {in_session}")
                        
                        hospitals_assigned += 1
                        logger.info(f"[HOSPITAL_ASSIGN] hospitals_assigned incremented to {hospitals_assigned}")

                except Exception as exc:
                    error_count += 1
                    logger.error(f"[HOSPITAL_ASSIGN_ERROR] Error: {str(exc)}", exc_info=True)

            # Add to details if anything was assigned
            if shift or hospital_name:
                details.append({
                    "emp_code": emp_code,
                    "emp_name": employee.name,
                    "shift_name": shift.name if shift else "—",
                    "hospital_name": hospital_name if hospital_name else "—",
                    "status": "assigned",
                    "reason": ""
                })

        # Log pending operations before commit
        logger.info(f"[PRE-COMMIT] db.session.new count: {len(db.session.new)}")
        logger.info(f"[PRE-COMMIT] db.session.dirty count: {len(db.session.dirty)}")
        logger.info(f"[PRE-COMMIT] db.session.deleted count: {len(db.session.deleted)}")
        
        hospital_objs = [obj for obj in db.session.new if isinstance(obj, EmployeeHospitalAssignment)]
        logger.info(f"[PRE-COMMIT] EmployeeHospitalAssignment NEW objects: {len(hospital_objs)}")
        for obj in hospital_objs:
            logger.info(f"  - emp_id={obj.employee_id}, hospital='{obj.hospital_name}'")
        
        dirty_hospital_objs = [obj for obj in db.session.dirty if isinstance(obj, EmployeeHospitalAssignment)]
        logger.info(f"[PRE-COMMIT] EmployeeHospitalAssignment DIRTY objects: {len(dirty_hospital_objs)}")
        for obj in dirty_hospital_objs:
            logger.info(f"  - emp_id={obj.employee_id}, hospital='{obj.hospital_name}', effective_until={obj.effective_until}")

        # Commit all changes
        try:
            db.session.commit()
            logger.info(f"[COMMIT-SUCCESS] Database committed successfully")
        except Exception as exc:
            db.session.rollback()
            logger.error(f"[COMMIT-FAILED] Import commit failed: {str(exc)}")
            return {
                "success": False,
                "message": f"Database error: {exc}"
            }

        logger.info(f"[IMPORT_COMPLETE] shifts={assigned}, hospitals={hospitals_assigned}, skipped={skipped}, not_found={not_found}, errors={error_count}")

        return {
            "success":    True,
            "message":    f"Import complete. {assigned} shifts assigned, {hospitals_assigned} hospitals assigned, {skipped} skipped, {not_found} not found, {error_count} errors.",
            "assigned":   assigned,
            "hospitals_assigned": hospitals_assigned,
            "skipped":    skipped,
            "notfound":   not_found,
            "errors":     error_count,
            "total":      len(rows),
            "details":    details,
        }

    def _match_shift(self, shift_input: str) -> Optional[Shift]:
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

        original_input = shift_input
        shift_input_upper = shift_input.strip().upper()

        logger.info(f"[SHIFT_MATCH] Looking for shift: '{original_input}'")

        # Strategy 1: Exact match by name (case-insensitive)
        shift = Shift.query.filter(
            Shift.name.ilike(shift_input_upper),
            Shift.is_active == True,
            Shift.is_deleted == False
        ).first()
        if shift:
            logger.info(f"[SHIFT_MATCH] Strategy 1 (exact name): FOUND - {shift.name}")
            return shift

        # Strategy 2: Exact match by code (case-insensitive)
        shift = Shift.query.filter(
            Shift.code.ilike(shift_input_upper),
            Shift.is_active == True,
            Shift.is_deleted == False
        ).first()
        if shift:
            logger.info(f"[SHIFT_MATCH] Strategy 2 (exact code): FOUND - {shift.name}")
            return shift

        # Strategy 3: Partial match by name (contains) - case insensitive
        shift = Shift.query.filter(
            Shift.name.ilike(f"%{shift_input_upper}%"),
            Shift.is_active == True,
            Shift.is_deleted == False
        ).first()
        if shift:
            logger.info(f"[SHIFT_MATCH] Strategy 3 (partial name): FOUND - {shift.name}")
            return shift

        # Strategy 4: Try to match time range pattern (e.g., "11:00 AM to 08:00 PM")
        shift = self._match_by_time_range(shift_input)
        if shift:
            logger.info(f"[SHIFT_MATCH] Strategy 4 (time range): FOUND - {shift.name}")
            return shift

        logger.warning(f"[SHIFT_MATCH] NO MATCH FOUND for: '{original_input}'")
        return None

    def _match_by_time_range(self, shift_input: str) -> Optional[Shift]:
        """
        Try to match shift by time range pattern.
        E.g., "11:00 AM to 08:00 PM" → find shift with matching start/end times
        """
        try:
            import re
            match = re.search(
                r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)\s*to\s*(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)',
                shift_input,
                re.IGNORECASE
            )
            if not match:
                logger.debug(f"No time range pattern found in: {shift_input}")
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

            from datetime import time as dt_time
            start_time = dt_time(start_h, start_m)
            end_time = dt_time(end_h, end_m)

            logger.debug(f"Parsed time range: {start_time} to {end_time}")

            shift = Shift.query.filter(
                Shift.start_time == start_time,
                Shift.end_time == end_time,
                Shift.is_active == True,
                Shift.is_deleted == False
            ).first()
            
            if shift:
                logger.info(f"Matched shift by time range: {shift.name}")
            else:
                logger.warning(f"No shift found for time range {start_time} to {end_time}")
            
            return shift

        except Exception as e:
            logger.warning(f"Time range matching failed for '{shift_input}': {e}")
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
        
        logger.info(f"[PARSE_SHEET] Headers found: {headers}")

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
                logger.info(f"[PARSE_SHEET] Found SHIFT column: '{shift_col_name}'")
                break

        # Check for hospital column (accept multiple names)
        hospital_col_found = False
        hospital_col_name = None
        for col_name in self.HOSPITAL_COLUMN_NAMES:
            if col_name in headers:
                hospital_col_found = True
                hospital_col_name = col_name
                logger.info(f"[PARSE_SHEET] Found HOSPITAL column: '{hospital_col_name}'")
                break

        if not shift_col_found and not hospital_col_found:
            error_msg = f"Missing columns: Need at least SHIFT or HOSPITAL. Found: {', '.join(headers[:10])}"
            logger.error(f"[PARSE_SHEET] {error_msg}")
            return [], [], [error_msg]

        emp_code_idx = headers.index("EMP-CODE")
        shift_idx = headers.index(shift_col_name) if shift_col_found else None
        hospital_idx = headers.index(hospital_col_name) if hospital_col_found else None
        
        logger.info(f"[PARSE_SHEET] Indices: emp={emp_code_idx}, shift={shift_idx}, hospital={hospital_idx}")

        rows = []
        for sheet_row_num, sheet_row in enumerate(rows_iter, start=2):
            vals = [cell.value for cell in sheet_row]
            if not any(vals):
                continue

            emp_code = str(vals[emp_code_idx]).strip() if len(vals) > emp_code_idx and vals[emp_code_idx] else ""
            shift_input = str(vals[shift_idx]).strip() if shift_idx is not None and len(vals) > shift_idx and vals[shift_idx] else ""
            hospital_input = str(vals[hospital_idx]).strip() if hospital_idx is not None and len(vals) > hospital_idx and vals[hospital_idx] else ""

            if emp_code and emp_code.lower() not in ("none", "nan", "emp-code"):
                row_data = {
                    "EMP-CODE": emp_code,
                    "SHIFT": shift_input,
                    "HOSPITAL": hospital_input
                }
                rows.append(row_data)

        logger.info(f"[PARSE_SHEET] Extracted {len(rows)} rows")
        return headers, rows, []

