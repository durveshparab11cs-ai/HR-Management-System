"""
admin/employee_import.py
==========================
Service for importing employees from Excel into the EmployeeMaster table.

Handles:
    - Reading Excel via openpyxl
    - Validating required columns
    - Detecting duplicates
    - Bulk import with detailed report
"""

import logging
from typing import Optional

import openpyxl
from werkzeug.datastructures import FileStorage

from app.extensions.database import db
from app.models.employee_master import EmployeeMaster

logger = logging.getLogger(__name__)


class EmployeeImportService:

    REQUIRED_COLUMNS = {"EMP-CODE", "NAME"}

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
            logger.error("Excel preview failed: %s", exc)
            return {"success": False, "message": f"Could not read file: {exc}", "errors": [str(exc)]}

    def import_from_file(self, file: FileStorage, imported_by: int = 1) -> dict:
        """
        Full import: read Excel, validate, deduplicate, insert.

        Returns import summary:
            {
                imported:  int,
                skipped:   int,    # already in DB
                duplicate: int,    # duplicate in file
                errors:    int,
                details:   list of {code, name, status, reason}
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

        imported    = 0
        skipped     = 0
        duplicates  = 0
        error_count = 0
        details     = []
        seen_codes  = set()

        for row in rows:
            code = (row.get("EMP-CODE") or "").strip().upper()
            name = (row.get("NAME") or "").strip()

            if not code or not name:
                error_count += 1
                details.append({"code": code or "?", "name": name or "?",
                                 "status": "error", "reason": "Missing code or name"})
                continue

            # Duplicate within the file
            if code in seen_codes:
                duplicates += 1
                details.append({"code": code, "name": name,
                                 "status": "duplicate", "reason": "Duplicate in file"})
                continue
            seen_codes.add(code)

            # Already in DB
            existing = EmployeeMaster.query.filter_by(employee_code=code).first()
            if existing:
                skipped += 1
                details.append({"code": code, "name": name,
                                 "status": "skipped", "reason": "Already exists in system"})
                continue

            # Insert
            try:
                master = EmployeeMaster(
                    employee_code=code,
                    employee_name=name,
                )
                db.session.add(master)
                imported += 1
                details.append({"code": code, "name": name, "status": "imported", "reason": ""})
            except Exception as exc:
                error_count += 1
                details.append({"code": code, "name": name,
                                 "status": "error", "reason": str(exc)})

        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            return {"success": False, "message": f"Database error: {exc}"}

        logger.info("EMPLOYEE_IMPORT | imported=%s | skipped=%s | dup=%s | errors=%s",
                    imported, skipped, duplicates, error_count)

        return {
            "success":    True,
            "message":    f"Import complete. {imported} imported, {skipped} skipped, {duplicates} duplicates, {error_count} errors.",
            "imported":   imported,
            "skipped":    skipped,
            "duplicate":  duplicates,
            "errors":     error_count,
            "total":      len(rows),
            "details":    details,
        }

    def _parse_sheet(self, ws) -> tuple:
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

        missing = self.REQUIRED_COLUMNS - set(headers)
        if missing:
            return [], [], [
                f"Missing required columns: {', '.join(missing)}. "
                f"Found: {', '.join(headers[:10])}"
            ]

        code_idx = headers.index("EMP-CODE")
        name_idx = headers.index("NAME")

        rows = []
        for sheet_row in rows_iter:
            vals = [cell.value for cell in sheet_row]
            if not any(vals):
                continue
            code = str(vals[code_idx]).strip() if len(vals) > code_idx and vals[code_idx] else ""
            name = str(vals[name_idx]).strip() if len(vals) > name_idx and vals[name_idx] else ""
            if code and code.lower() not in ("none", "nan", "emp-code"):
                rows.append({"EMP-CODE": code, "NAME": name})

        return headers, rows, []
