"""
admin/employee_import.py
==========================
Enterprise Service for importing employees from CSV or Excel into the EmployeeMaster table.

Handles:
    - Reading CSV (UTF-8, ISO-8859-1) and Excel (.xlsx, .xls via openpyxl)
    - Flexible column header aliases
    - Reporting which columns are present and which are missing
    - Validation preview before committing
    - Deduplication (within file and against DB)
    - Atomic transaction with rollback support
    - Rollback of specific import batches
"""

import csv
import io
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List

import openpyxl
from werkzeug.datastructures import FileStorage

from app.extensions.database import db
from app.models.employee_master import EmployeeMaster

logger = logging.getLogger(__name__)


# Standard schema fields and their accepted header aliases (case-insensitive)
COLUMN_ALIASES = {
    "code": [
        "EMPLOYEE CODE", "EMP-CODE", "EMP_CODE", "EMPLOYEE_CODE",
        "CODE", "EMP ID", "EMPLOYEE ID", "EMPID"
    ],
    "name": [
        "EMPLOYEE NAME", "NAME", "EMPLOYEE_NAME", "FULL NAME",
        "FULL_NAME", "STAFF NAME"
    ],
    "department": [
        "DEPARTMENT", "DEPT", "DEPT_NAME", "DEPARTMENT NAME"
    ],
    "designation": [
        "DESIGNATION", "ROLE", "POSITION", "TITLE", "JOB TITLE"
    ],
    "working_location": [
        "WORKING LOCATION", "WORKING_LOCATION", "LOCATION",
        "HOSPITAL", "SITE", "HOSPITAL LOCATION", "BRANCH"
    ],
    "shift_timing": [
        "SHIFT TIMING", "FULL SHIFT TIMING", "SHIFT_TIMING",
        "SHIFT", "TIMING", "ASSIGNED SHIFT"
    ],
    "working_status": [
        "WORKING STATUS", "WORKING_STATUS", "STATUS",
        "EMPLOYMENT STATUS", "ACTIVE STATUS"
    ],
}

STANDARD_COLUMNS = [
    ("code", "Employee Code (Required)"),
    ("name", "Employee Name (Required)"),
    ("department", "Department"),
    ("designation", "Designation"),
    ("working_location", "Working Location / Hospital"),
    ("shift_timing", "Shift Timing"),
    ("working_status", "Working Status"),
]


class EmployeeImportService:

    def _normalize_header(self, raw_header: str) -> str:
        """Strip and normalize header string."""
        if not raw_header:
            return ""
        return " ".join(str(raw_header).strip().replace("_", " ").replace("-", " ").split()).upper()

    def _map_columns(self, raw_headers: List[str]) -> Tuple[Dict[str, int], List[str], List[str]]:
        """
        Map file headers to internal field names using aliases.
        Returns:
            (col_map, present_labels, missing_labels)
        """
        col_map = {}
        present_fields = set()

        normalized_headers = [self._normalize_header(h) for h in raw_headers]

        for field, aliases in COLUMN_ALIASES.items():
            norm_aliases = [self._normalize_header(a) for a in aliases]
            for idx, h in enumerate(normalized_headers):
                if h in norm_aliases:
                    col_map[field] = idx
                    present_fields.add(field)
                    break

        present_labels = [label for field, label in STANDARD_COLUMNS if field in present_fields]
        missing_labels = [label for field, label in STANDARD_COLUMNS if field not in present_fields]

        return col_map, present_labels, missing_labels

    def _read_data_from_source(self, source: Any) -> Tuple[List[str], List[List[Any]], Optional[str]]:
        """
        Read headers and rows from a FileStorage, filepath, or file-like object.
        Supports .csv, .xlsx, .xls.
        """
        filename = getattr(source, "filename", "") or (source if isinstance(source, str) else "")
        filename_lower = filename.lower()

        if filename_lower.endswith(".csv") or isinstance(source, (str, io.TextIOBase, io.StringIO)):
            # Read CSV
            try:
                if isinstance(source, str):
                    with open(source, "r", encoding="utf-8", errors="replace") as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                elif hasattr(source, "read"):
                    content = source.read()
                    if isinstance(content, bytes):
                        try:
                            text = content.decode("utf-8")
                        except UnicodeDecodeError:
                            text = content.decode("latin-1")
                    else:
                        text = content
                    reader = csv.reader(io.StringIO(text))
                    rows = list(reader)
                else:
                    return [], [], "Unsupported source format"

                if not rows:
                    return [], [], "CSV file is empty"

                headers = [str(c).strip() for c in rows[0]]
                data_rows = rows[1:]
                return headers, data_rows, None
            except Exception as e:
                return [], [], f"Failed to parse CSV: {str(e)}"

        elif filename_lower.endswith((".xlsx", ".xls")):
            # Read Excel
            try:
                wb = openpyxl.load_workbook(source, read_only=True, data_only=True)
                ws = wb.active
                rows_iter = iter(ws.rows)
                try:
                    header_row = next(rows_iter)
                except StopIteration:
                    return [], [], "Excel file appears to be empty."

                headers = [str(cell.value).strip() if cell.value is not None else "" for cell in header_row]
                data_rows = []
                for row in rows_iter:
                    vals = [cell.value for cell in row]
                    if any(v is not None and str(v).strip() != "" for v in vals):
                        data_rows.append(vals)
                return headers, data_rows, None
            except Exception as e:
                return [], [], f"Failed to parse Excel file: {str(e)}"
        else:
            return [], [], f"Unsupported file type. Please upload a .csv, .xlsx, or .xls file."

    def preview(self, source: Any) -> Dict[str, Any]:
        """
        Analyze file and return preview without committing to DB.
        Includes column presence report and duplicate checks.
        """
        headers, data_rows, error = self._read_data_from_source(source)
        if error:
            return {"success": False, "message": error, "errors": [error]}

        col_map, present_labels, missing_labels = self._map_columns(headers)

        if "code" not in col_map or "name" not in col_map:
            missing_req = []
            if "code" not in col_map:
                missing_req.append("Employee Code")
            if "name" not in col_map:
                missing_req.append("Employee Name")
            return {
                "success": False,
                "message": f"Required columns missing: {', '.join(missing_req)}",
                "headers": headers,
                "present_columns": present_labels,
                "missing_columns": missing_labels,
                "errors": [f"Missing required columns: {', '.join(missing_req)}. Detected headers: {headers[:8]}"]
            }

        code_idx = col_map["code"]
        name_idx = col_map["name"]

        preview_rows = []
        seen_in_file = set()
        db_existing_codes = set(
            c[0].upper() for c in db.session.query(EmployeeMaster.employee_code).all()
        )

        valid_count = 0
        dup_file_count = 0
        already_db_count = 0

        for r_idx, row in enumerate(data_rows):
            code_raw = str(row[code_idx]).strip() if len(row) > code_idx and row[code_idx] is not None else ""
            name_raw = str(row[name_idx]).strip() if len(row) > name_idx and row[name_idx] is not None else ""

            if not code_raw or code_raw.lower() in ("nan", "none", "null"):
                continue

            code_norm = code_raw.upper()
            status = "valid"
            reason = ""

            if code_norm in seen_in_file:
                status = "duplicate_in_file"
                reason = "Repeated code in this file"
                dup_file_count += 1
            elif code_norm in db_existing_codes:
                status = "already_in_db"
                reason = "Already registered in Employee Master"
                already_db_count += 1
            else:
                valid_count += 1

            seen_in_file.add(code_norm)

            if len(preview_rows) < 15:
                preview_rows.append({
                    "code": code_norm,
                    "name": name_raw or "N/A",
                    "department": str(row[col_map["department"]]).strip() if "department" in col_map and len(row) > col_map["department"] and row[col_map["department"]] else "—",
                    "designation": str(row[col_map["designation"]]).strip() if "designation" in col_map and len(row) > col_map["designation"] and row[col_map["designation"]] else "—",
                    "location": str(row[col_map["working_location"]]).strip() if "working_location" in col_map and len(row) > col_map["working_location"] and row[col_map["working_location"]] else "—",
                    "status": status,
                    "reason": reason
                })

        return {
            "success": True,
            "message": f"{len(data_rows)} rows found. {valid_count} new employees ready to import.",
            "total_rows": len(data_rows),
            "valid_count": valid_count,
            "duplicate_in_file_count": dup_file_count,
            "already_in_db_count": already_db_count,
            "headers": headers,
            "present_columns": present_labels,
            "missing_columns": missing_labels,
            "preview_rows": preview_rows
        }

    def import_from_source(self, source: Any, imported_by: int = 1) -> Dict[str, Any]:
        """
        Execute atomic import with rollback safety.
        Returns detailed summary and batch ID.
        """
        headers, data_rows, error = self._read_data_from_source(source)
        if error:
            return {"success": False, "message": error}

        col_map, present_labels, missing_labels = self._map_columns(headers)
        if "code" not in col_map or "name" not in col_map:
            return {"success": False, "message": "Required columns (Employee Code, Employee Name) missing."}

        code_idx = col_map["code"]
        name_idx = col_map["name"]

        batch_id = datetime.utcnow().strftime("BATCH-%Y%m%d-%H%M%S")
        import_timestamp = datetime.utcnow()

        imported = 0
        skipped = 0
        duplicates = 0
        errors = 0
        details = []
        seen_codes = set()

        existing_in_db = {
            c[0].upper(): c[0] for c in db.session.query(EmployeeMaster.employee_code).all()
        }

        try:
            for row in data_rows:
                code_raw = str(row[code_idx]).strip() if len(row) > code_idx and row[code_idx] is not None else ""
                name_raw = str(row[name_idx]).strip() if len(row) > name_idx and row[name_idx] is not None else ""

                if not code_raw or code_raw.lower() in ("nan", "none", "null"):
                    continue

                code = code_raw.upper()
                name = name_raw

                if not name:
                    errors += 1
                    details.append({"code": code, "name": "Missing", "status": "error", "reason": "Missing employee name"})
                    continue

                if code in seen_codes:
                    duplicates += 1
                    details.append({"code": code, "name": name, "status": "duplicate", "reason": "Duplicate within file"})
                    continue
                seen_codes.add(code)

                if code in existing_in_db:
                    skipped += 1
                    details.append({"code": code, "name": name, "status": "skipped", "reason": "Already exists in Employee Master"})
                    continue

                # Extract optional fields
                def get_val(field):
                    if field in col_map and len(row) > col_map[field]:
                        v = row[col_map[field]]
                        if v is not None and str(v).strip().lower() not in ("nan", "none", ""):
                            return str(v).strip()
                    return None

                master = EmployeeMaster(
                    employee_code=code,
                    employee_name=name,
                    department=get_val("department"),
                    designation=get_val("designation"),
                    working_location=get_val("working_location"),
                    shift_timing=get_val("shift_timing"),
                    working_status=get_val("working_status") or "Active",
                    is_registered=False,
                    is_active=True,
                    imported_at=import_timestamp
                )
                db.session.add(master)
                imported += 1
                details.append({"code": code, "name": name, "status": "imported", "reason": ""})

            db.session.commit()
            logger.info("EMPLOYEE_IMPORT_SUCCESS | batch=%s | imported=%d | skipped=%d | duplicates=%d",
                        batch_id, imported, skipped, duplicates)

            return {
                "success": True,
                "batch_id": batch_id,
                "message": f"Successfully imported {imported} new employees. {skipped} already existed, {duplicates} duplicate in file.",
                "imported": imported,
                "skipped": skipped,
                "duplicate": duplicates,
                "errors": errors,
                "total": len(data_rows),
                "present_columns": present_labels,
                "missing_columns": missing_labels,
                "details": details[:50]
            }

        except Exception as exc:
            db.session.rollback()
            logger.error("EMPLOYEE_IMPORT_FAILED | error=%s", exc, exc_info=True)
            return {"success": False, "message": f"Database import error: {str(exc)}"}

    import_from_file = import_from_source

    def rollback_since(self, since_timestamp: datetime) -> Dict[str, Any]:
        """Rollback employees imported since a specific timestamp."""
        try:
            deleted_count = EmployeeMaster.query.filter(
                EmployeeMaster.imported_at >= since_timestamp,
                EmployeeMaster.is_registered == False  # Never delete already registered employees
            ).delete()
            db.session.commit()
            return {"success": True, "deleted_count": deleted_count, "message": f"Rolled back {deleted_count} imported records."}
        except Exception as exc:
            db.session.rollback()
            return {"success": False, "message": f"Rollback failed: {str(exc)}"}
