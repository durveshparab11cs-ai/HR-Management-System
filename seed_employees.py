"""
seed_employees.py
==================
One-shot script to seed EmployeeMaster from Book1.xlsx.

Usage (from smart_hrms/ folder):
    python seed_employees.py
    python seed_employees.py --file path/to/Book1.xlsx
    python seed_employees.py --dry-run

The script looks for Book1.xlsx in the following locations (in order):
    1. Current directory  (smart_hrms/)
    2. Parent directory   (HR management system/)
    3. --file argument

Requirements:
    pip install openpyxl
"""

import os
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Resolve Excel path ────────────────────────────────────────────────

DEFAULT_SEARCH_PATHS = [
    "Book1.xlsx",
    "../Book1.xlsx",
    os.path.join(os.path.dirname(__file__), "Book1.xlsx"),
    os.path.join(os.path.dirname(__file__), "..", "Book1.xlsx"),
]


def find_excel(explicit_path: str = None) -> str:
    if explicit_path:
        if not os.path.exists(explicit_path):
            log.error("File not found: %s", explicit_path)
            sys.exit(1)
        return explicit_path

    for p in DEFAULT_SEARCH_PATHS:
        if os.path.exists(p):
            log.info("Found Excel at: %s", os.path.abspath(p))
            return p

    log.error(
        "Book1.xlsx not found. Provide path via --file or place it in the smart_hrms/ folder."
    )
    sys.exit(1)


# ── Parse columns ─────────────────────────────────────────────────────

def parse_excel(path: str) -> list:
    """
    Parse Book1.xlsx and return list of {employee_code, employee_name} dicts.

    Accepts column headers (case-insensitive):
        EMP-CODE / EMPCODE / EMPLOYEE CODE / CODE  → employee_code
        NAME / EMPLOYEE NAME / FULL NAME           → employee_name
    """
    try:
        import openpyxl
    except ImportError:
        log.error("openpyxl not installed. Run: pip install openpyxl")
        sys.exit(1)

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.rows)
    if not rows:
        log.error("Excel file is empty.")
        sys.exit(1)

    # -- detect header row --
    raw_headers = [str(c.value).strip() if c.value else "" for c in rows[0]]
    headers_upper = [h.upper() for h in raw_headers]

    CODE_ALIASES = {"EMP-CODE", "EMPCODE", "EMP CODE", "EMPLOYEE CODE", "CODE", "EMP_CODE"}
    NAME_ALIASES = {"NAME", "EMPLOYEE NAME", "FULL NAME", "EMPNAME", "EMP NAME", "EMP_NAME"}

    code_idx = next((i for i, h in enumerate(headers_upper) if h in CODE_ALIASES), None)
    name_idx = next((i for i, h in enumerate(headers_upper) if h in NAME_ALIASES), None)

    if code_idx is None:
        log.error(
            "Cannot find Employee Code column. Headers found: %s\n"
            "Expected one of: %s",
            raw_headers,
            sorted(CODE_ALIASES),
        )
        sys.exit(1)

    if name_idx is None:
        log.error(
            "Cannot find Employee Name column. Headers found: %s\n"
            "Expected one of: %s",
            raw_headers,
            sorted(NAME_ALIASES),
        )
        sys.exit(1)

    log.info("Using column #%d for code, #%d for name", code_idx + 1, name_idx + 1)

    records = []
    for i, row in enumerate(rows[1:], start=2):  # skip header
        vals = [c.value for c in row]
        code = str(vals[code_idx]).strip() if len(vals) > code_idx and vals[code_idx] else ""
        name = str(vals[name_idx]).strip() if len(vals) > name_idx and vals[name_idx] else ""

        # Skip empty or obviously bad rows
        if not code or code.lower() in ("none", "nan", "emp-code", "code"):
            continue
        if not name or name.lower() in ("none", "nan", "name"):
            continue

        records.append({
            "employee_code": code.upper(),
            "employee_name": name,
        })

    log.info("Parsed %d valid rows from Excel.", len(records))
    return records


# ── Seed into DB ──────────────────────────────────────────────────────

def seed(records: list, dry_run: bool = False) -> None:
    """Import records into EmployeeMaster, skipping duplicates."""
    # Bootstrap Flask app
    sys.path.insert(0, os.path.dirname(__file__))
    os.environ.setdefault("FLASK_ENV", "development")

    try:
        from app import create_app
    except ImportError as e:
        log.error("Cannot import app: %s", e)
        sys.exit(1)

    app = create_app("development")

    with app.app_context():
        from app.extensions.database import db
        from app.models.employee_master import EmployeeMaster

        # Ensure table exists
        db.create_all()

        imported   = 0
        skipped    = 0
        errors     = 0
        duplicates_in_file = 0
        seen       = set()

        for rec in records:
            code = rec["employee_code"]
            name = rec["employee_name"]

            # Duplicate within file
            if code in seen:
                duplicates_in_file += 1
                log.warning("DUPLICATE_IN_FILE  code=%-20s  name=%s", code, name)
                continue
            seen.add(code)

            # Already in DB
            if EmployeeMaster.query.filter_by(employee_code=code).first():
                skipped += 1
                continue

            if dry_run:
                log.info("DRY-RUN  WOULD-IMPORT  code=%-20s  name=%s", code, name)
                imported += 1
                continue

            try:
                master = EmployeeMaster(
                    employee_code=code,
                    employee_name=name,
                )
                db.session.add(master)
                imported += 1
            except Exception as exc:
                errors += 1
                log.error("ERROR  code=%s  error=%s", code, exc)

        if not dry_run:
            try:
                db.session.commit()
                log.info("Database committed.")
            except Exception as exc:
                db.session.rollback()
                log.error("Commit failed: %s", exc)
                sys.exit(1)

    # ── Summary ───────────────────────────────────────────────────────
    print()
    print("=" * 50)
    print("  SEED SUMMARY")
    print("=" * 50)
    print(f"  Total rows parsed  : {len(records)}")
    print(f"  Imported           : {imported}")
    print(f"  Skipped (exist)    : {skipped}")
    print(f"  Duplicates in file : {duplicates_in_file}")
    print(f"  Errors             : {errors}")
    if dry_run:
        print()
        print("  *** DRY RUN — nothing written to database ***")
    print("=" * 50)
    print()


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Seed Smart HRMS EmployeeMaster from Book1.xlsx"
    )
    parser.add_argument(
        "--file", "-f",
        metavar="PATH",
        help="Path to Excel file (default: auto-detect Book1.xlsx)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview without writing to database",
    )
    args = parser.parse_args()

    excel_path = find_excel(args.file)
    records    = parse_excel(excel_path)

    if not records:
        log.error("No valid records found in Excel. Nothing to import.")
        sys.exit(1)

    seed(records, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
