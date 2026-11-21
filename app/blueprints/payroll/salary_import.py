"""
app/blueprints/payroll/salary_import.py
=======================================
Enterprise Salary Structure Master Import Service.

Enables HR and Super Admins to upload Excel (.xlsx, .xls) or CSV files with:
  1. Employee Code (e.g. E-2606026)
  2. Employee Name
  3. Salary Amount (Monthly Gross / CTC)
  4. PF (Provident Fund deduction)
  5. TDS (Tax Deducted at Source)
  6. PT (Professional Tax deduction, default ₹200)

Handles:
  - Robust column mapping with alias support
  - Clean currency/number parsing (handles commas, currency symbols, percentages)
  - Upsert (creates new records or updates existing salary structures)
  - Automatic linkage to Employee records
  - Instant Net Salary calculation: Gross - (PF + TDS + PT)
  - Detailed import report (imported, updated, errors)
  - Excel sample template generator with valid real employee references
"""

import io
import logging
from typing import Dict, Any, List, Tuple, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from werkzeug.datastructures import FileStorage

from app.extensions.database import db
from app.models.employee import Employee
from app.models.employee_master import EmployeeMaster
from app.models.payroll import EmployeeSalaryMaster

logger = logging.getLogger(__name__)

# Column aliases for flexible Excel matching
COLUMN_ALIASES = {
    "code": [
        "EMPLOYEE CODE", "EMP CODE", "EMP-CODE", "EMP_CODE",
        "CODE", "EMPLOYEE ID", "EMP ID", "EMPID"
    ],
    "name": [
        "EMPLOYEE NAME", "NAME", "FULL NAME", "STAFF NAME",
        "EMPLOYEE_NAME", "FULL_NAME", "EMP NAME"
    ],
    "salary": [
        "SALARY AMOUNT", "SALARY", "GROSS SALARY", "GROSS",
        "CTC", "MONTHLY SALARY", "SALARY_AMOUNT", "AMOUNT",
        "BASE SALARY", "BASIC SALARY", "MONTHLY GROSS"
    ],
    "pf": [
        "PF", "PF AMOUNT", "PF_AMOUNT", "PROVIDENT FUND",
        "PF DEDUCTION", "EPF", "EPF AMOUNT"
    ],
    "tds": [
        "TDS", "TDS AMOUNT", "TDS_AMOUNT", "TAX", "TAX DEDUCTION",
        "INCOME TAX", "TAX DEDUCTED AT SOURCE", "IT DEDUCTION"
    ],
    "pt": [
        "PT", "PROFESSIONAL TAX", "PT AMOUNT", "PT_AMOUNT",
        "PROF TAX", "P.T.", "PROFESSIONAL_TAX"
    ],
}


class SalaryImportService:
    """Service to handle Excel / CSV salary master structure importation."""

    @staticmethod
    def _normalize(text: Any) -> str:
        if text is None:
            return ""
        return " ".join(str(text).strip().replace("_", " ").replace("-", " ").split()).upper()

    @staticmethod
    def _clean_number(val: Any, default: float = 0.0) -> float:
        """Parse numeric values from strings, handling commas, currencies, spaces."""
        if val is None:
            return default
        if isinstance(val, (int, float)):
            return float(val)
        
        s = str(val).strip().replace(",", "").replace("₹", "").replace("$", "")
        if not s:
            return default
        try:
            return float(s)
        except (ValueError, TypeError):
            return default

    def _map_columns(self, headers: List[str]) -> Tuple[Dict[str, int], List[str]]:
        """Map raw header names to known fields."""
        norm_headers = [self._normalize(h) for h in headers]
        col_map: Dict[str, int] = {}
        missing_required = []

        for field, aliases in COLUMN_ALIASES.items():
            for idx, h in enumerate(norm_headers):
                if h in [self._normalize(a) for a in aliases]:
                    col_map[field] = idx
                    break

        if "code" not in col_map:
            missing_required.append("Employee Code (e.g. EMP-CODE, EMPLOYEE ID)")
        if "salary" not in col_map:
            missing_required.append("Salary Amount (e.g. SALARY, GROSS, CTC)")

        return col_map, missing_required

    def _extract_rows(self, file_storage: FileStorage) -> Tuple[List[str], List[List[Any]]]:
        """Extract headers and data rows from Excel or CSV."""
        filename = (file_storage.filename or "").lower()
        file_bytes = file_storage.read()
        file_storage.seek(0)

        if filename.endswith((".xlsx", ".xls")):
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                return [], []
            headers = [str(cell) if cell is not None else "" for cell in rows[0]]
            data_rows = [list(r) for r in rows[1:] if any(c is not None and str(c).strip() for c in r)]
            return headers, data_rows
        elif filename.endswith(".csv"):
            text = None
            for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
                try:
                    text = file_bytes.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            if not text:
                text = file_bytes.decode("utf-8", errors="replace")

            import csv
            reader = list(csv.reader(io.StringIO(text)))
            if not reader:
                return [], []
            headers = [str(c) for c in reader[0]]
            data_rows = [r for r in reader[1:] if any(c.strip() for c in r)]
            return headers, data_rows
        else:
            raise ValueError("Unsupported file format. Please upload .xlsx, .xls, or .csv")

    def preview(self, file_storage: FileStorage) -> Dict[str, Any]:
        """Preview first 10 rows from uploaded file without saving."""
        try:
            headers, data_rows = self._extract_rows(file_storage)
            if not headers:
                return {"success": False, "error": "Uploaded file is empty or has no header row."}

            col_map, missing_required = self._map_columns(headers)
            if missing_required:
                return {
                    "success": False,
                    "error": f"Missing required columns: {', '.join(missing_required)}",
                    "detected_headers": headers
                }

            preview_items = []
            for row in data_rows[:15]:
                code_raw = row[col_map["code"]] if "code" in col_map and col_map["code"] < len(row) else ""
                name_raw = row[col_map["name"]] if "name" in col_map and col_map["name"] < len(row) else ""
                salary_raw = row[col_map["salary"]] if "salary" in col_map and col_map["salary"] < len(row) else 0
                pf_raw = row[col_map["pf"]] if "pf" in col_map and col_map["pf"] < len(row) else 0
                tds_raw = row[col_map["tds"]] if "tds" in col_map and col_map["tds"] < len(row) else 0
                pt_raw = row[col_map["pt"]] if "pt" in col_map and col_map["pt"] < len(row) else 200

                code = str(code_raw).strip() if code_raw is not None else ""
                if not code:
                    continue

                salary = self._clean_number(salary_raw, 0.0)
                pf = self._clean_number(pf_raw, 0.0)
                tds = self._clean_number(tds_raw, 0.0)
                pt = self._clean_number(pt_raw, 200.0) if pt_raw is not None and str(pt_raw).strip() != "" else 200.0
                net = max(0.0, round(salary - (pf + tds + pt), 2))

                preview_items.append({
                    "code": code,
                    "name": str(name_raw or "—").strip(),
                    "salary": salary,
                    "pf": pf,
                    "tds": tds,
                    "pt": pt,
                    "net": net,
                })

            return {
                "success": True,
                "total_rows": len(data_rows),
                "preview_items": preview_items,
                "detected_columns": list(col_map.keys()),
            }
        except Exception as exc:
            logger.exception("Preview failed for salary import")
            return {"success": False, "error": str(exc)}

    def import_file(self, file_storage: FileStorage) -> Dict[str, Any]:
        """Parse Excel/CSV and upsert EmployeeSalaryMaster records."""
        try:
            headers, data_rows = self._extract_rows(file_storage)
            if not headers:
                return {"success": False, "error": "Uploaded file is empty or has no header row."}

            col_map, missing_required = self._map_columns(headers)
            if missing_required:
                return {
                    "success": False,
                    "error": f"Missing required columns: {', '.join(missing_required)}",
                    "detected_headers": headers
                }

            imported_count = 0
            updated_count = 0
            error_count = 0
            details = []

            for row_idx, row in enumerate(data_rows, start=2):
                code_raw = row[col_map["code"]] if "code" in col_map and col_map["code"] < len(row) else None
                name_raw = row[col_map["name"]] if "name" in col_map and col_map["name"] < len(row) else ""
                salary_raw = row[col_map["salary"]] if "salary" in col_map and col_map["salary"] < len(row) else 0
                pf_raw = row[col_map["pf"]] if "pf" in col_map and col_map["pf"] < len(row) else 0
                tds_raw = row[col_map["tds"]] if "tds" in col_map and col_map["tds"] < len(row) else 0
                pt_raw = row[col_map["pt"]] if "pt" in col_map and col_map["pt"] < len(row) else 200

                if code_raw is None or not str(code_raw).strip():
                    continue

                code = str(code_raw).strip()
                name = str(name_raw or "").strip()

                # If name is blank, check if we can resolve it from EmployeeMaster or Employee
                if not name:
                    m = EmployeeMaster.query.filter_by(employee_code=code).first()
                    if m and m.employee_name:
                        name = m.employee_name
                    else:
                        emp = Employee.query.filter_by(employee_code=code).first()
                        if emp and emp.user:
                            name = emp.user.full_name
                        else:
                            name = f"Employee {code}"

                salary = self._clean_number(salary_raw, 0.0)
                if salary <= 0:
                    details.append({
                        "code": code,
                        "name": name,
                        "status": "error",
                        "message": f"Row {row_idx}: Invalid salary amount ({salary_raw})"
                    })
                    error_count += 1
                    continue

                pf = self._clean_number(pf_raw, 0.0)
                tds = self._clean_number(tds_raw, 0.0)
                pt = self._clean_number(pt_raw, 200.0) if pt_raw is not None and str(pt_raw).strip() != "" else 200.0
                net = max(0.0, round(salary - (pf + tds + pt), 2))

                # Lookup linked employee if exists
                emp = Employee.query.filter_by(employee_code=code).first()
                employee_id = emp.id if emp else None

                # Upsert EmployeeSalaryMaster
                record = EmployeeSalaryMaster.query.filter_by(employee_code=code).first()
                if record:
                    record.employee_name = name
                    record.employee_id = employee_id
                    record.salary_amount = salary
                    record.pf_amount = pf
                    record.tds_amount = tds
                    record.pt_amount = pt
                    record.net_salary = net
                    record.is_active = True
                    updated_count += 1
                    status_text = "updated"
                else:
                    record = EmployeeSalaryMaster(
                        employee_id=employee_id,
                        employee_code=code,
                        employee_name=name,
                        salary_amount=salary,
                        pf_amount=pf,
                        tds_amount=tds,
                        pt_amount=pt,
                        net_salary=net,
                        is_active=True
                    )
                    db.session.add(record)
                    imported_count += 1
                    status_text = "imported"

                details.append({
                    "code": code,
                    "name": name,
                    "status": status_text,
                    "salary": salary,
                    "net": net,
                    "message": f"Gross: ₹{salary:,.0f} | PF: ₹{pf:,.0f} | TDS: ₹{tds:,.0f} | PT: ₹{pt:,.0f} | Net: ₹{net:,.0f}"
                })

            db.session.commit()
            logger.info("SALARY_MASTER_IMPORT | imported=%d | updated=%d | errors=%d", imported_count, updated_count, error_count)

            return {
                "success": True,
                "total": imported_count + updated_count + error_count,
                "imported": imported_count,
                "updated": updated_count,
                "errors": error_count,
                "details": details
            }
        except Exception as exc:
            db.session.rollback()
            logger.exception("Failed to import salary structure master")
            return {"success": False, "error": str(exc)}

    @staticmethod
    def generate_sample_template() -> io.BytesIO:
        """
        Generate a professional, pre-styled Excel template with real sample employee codes.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Salary Master"

        # Styling
        header_fill = PatternFill(start_color="1A3C6E", end_color="1A3C6E", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        data_font = Font(name="Calibri", size=10)
        border_thin = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1")
        )
        currency_align = Alignment(horizontal="right", vertical="center")
        text_align = Alignment(horizontal="left", vertical="center")
        center_align = Alignment(horizontal="center", vertical="center")

        headers = ["Employee Code", "Employee Name", "Salary Amount", "PF", "TDS", "PT"]
        ws.append(headers)

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align
            cell.border = border_thin

        # Query top 5 real employees from EmployeeMaster to pre-fill realistic rows
        sample_rows = []
        try:
            real_masters = EmployeeMaster.query.limit(6).all()
            if real_masters:
                sample_salaries = [
                    (45000.0, 1800.0, 500.0, 200.0),
                    (38000.0, 1800.0, 300.0, 200.0),
                    (52000.0, 1800.0, 1200.0, 200.0),
                    (32000.0, 1800.0, 0.0, 200.0),
                    (65000.0, 1800.0, 2500.0, 200.0),
                    (28000.0, 1800.0, 0.0, 200.0),
                ]
                for idx, m in enumerate(real_masters):
                    sal, pf, tds, pt = sample_salaries[idx % len(sample_salaries)]
                    sample_rows.append([m.employee_code, m.employee_name, sal, pf, tds, pt])
        except Exception:
            pass

        if not sample_rows:
            sample_rows = [
                ["E-2606026", "Durvesh Parab", 45000.0, 1800.0, 500.0, 200.0],
                ["E-2512012", "Admin Staff", 38000.0, 1800.0, 300.0, 200.0],
                ["E-2603025", "HR Executive", 42000.0, 1800.0, 400.0, 200.0],
            ]

        for r_idx, row_data in enumerate(sample_rows, start=2):
            ws.append(row_data)
            for c_idx in range(1, len(row_data) + 1):
                c = ws.cell(row=r_idx, column=c_idx)
                c.font = data_font
                c.border = border_thin
                if c_idx in (1,):
                    c.alignment = center_align
                elif c_idx in (2,):
                    c.alignment = text_align
                else:
                    c.alignment = currency_align
                    c.number_format = "#,##0.00"

        # Adjust column widths
        col_widths = {1: 18, 2: 28, 3: 18, 4: 14, 5: 14, 6: 12}
        for col_idx, width in col_widths.items():
            col_letter = openpyxl.utils.get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = width

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output
