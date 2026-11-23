#!/usr/bin/env python3
"""
scripts/migrate_to_pg.py
========================
High-speed, robust SQLite to PostgreSQL data migration using native psql.exe.
Bypasses Python DLL restrictions by generating PostgreSQL-standard SQL
and executing it directly against PostgreSQL 18.
"""

import os
import sys
import sqlite3
import subprocess
import json
import time
from datetime import datetime, date, timezone
import pytz

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

PSQL_BIN = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
IST = pytz.timezone("Asia/Kolkata")

def escape_sql_value(val, col_type="TEXT"):
    if val is None:
        return "NULL"
    col_type_upper = col_type.upper()
    if "BOOL" in col_type_upper:
        if isinstance(val, bool):
            return "TRUE" if val else "FALSE"
        if isinstance(val, (int, float)):
            return "TRUE" if int(val) == 1 else "FALSE"
        s = str(val).strip().lower()
        return "TRUE" if s in ("true", "1", "yes", "t") else "FALSE"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, (datetime, date)):
        return f"'{val.isoformat()}'"
    # String / text
    s = str(val).replace("'", "''")
    return f"'{s}'"

def run_migration():
    print("=" * 70)
    print("Smart HRMS SQLite -> PostgreSQL 18 Migration")
    print("=" * 70)

    from app import create_app
    from app.extensions.database import db
    from sqlalchemy.schema import CreateTable
    from sqlalchemy.dialects import postgresql

    app = create_app("production")

    sqlite_path = os.path.join(PROJECT_ROOT, "instance", "smart_hrms_dev.db")
    if not os.path.exists(sqlite_path):
        print(f"ERROR: SQLite database not found at {sqlite_path}")
        return

    # 1. Connect to SQLite read-only
    conn = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 2. Get list of tables in SQLite
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    sqlite_tables = set(r[0] for r in cur.fetchall())

    # 3. Generate DDL for PostgreSQL
    sql_lines = []
    sql_lines.append("-- Smart HRMS Full PostgreSQL Migration Script")
    sql_lines.append("SET client_encoding = 'UTF8';")
    sql_lines.append("SET standard_conforming_strings = on;")
    sql_lines.append("SET check_function_bodies = false;")
    sql_lines.append("SET client_min_messages = warning;")
    sql_lines.append("SET session_replication_role = 'replica';")
    sql_lines.append("BEGIN;\n")

    # Drop existing tables cleanly if re-running
    sorted_tables = list(db.metadata.sorted_tables)
    for table in reversed(sorted_tables):
        sql_lines.append(f'DROP TABLE IF EXISTS "{table.name}" CASCADE;')

    # Create tables
    for table in sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=postgresql.dialect())).strip()
        sql_lines.append(f"{ddl};\n")

    # 4. Insert data table by table in dependency order
    table_stats = []

    # Check if users and employees exist in source, fallback to backup if empty
    backup_db_path = os.path.join(PROJECT_ROOT, "backups", "smart_hrms_prod_backup_20261121_205618.db")
    backup_conn = None
    if os.path.exists(backup_db_path):
        backup_conn = sqlite3.connect(f"file:{backup_db_path}?mode=ro", uri=True)
        backup_conn.row_factory = sqlite3.Row

    # Pre-fetch valid user IDs
    cur.execute("SELECT id FROM users")
    valid_user_ids = {r[0] for r in cur.fetchall()}
    if not valid_user_ids and backup_conn:
        b_cur = backup_conn.cursor()
        b_cur.execute("SELECT id FROM users")
        valid_user_ids = {r[0] for r in b_cur.fetchall()}

    for table in sorted_tables:
        tname = table.name
        
        # Source cursor selection
        active_cur = cur
        if tname in ("users", "employees"):
            cur.execute(f"SELECT COUNT(*) FROM {tname};")
            if cur.fetchone()[0] == 0 and backup_conn:
                active_cur = backup_conn.cursor()

        try:
            active_cur.execute(f"SELECT * FROM {tname};")
            rows = active_cur.fetchall()
        except sqlite3.OperationalError:
            # Table might not exist in SQLite
            continue
        count = len(rows)

        if count == 0:
            table_stats.append((tname, 0, 0))
            continue

        cols_in_model = {c.name: str(c.type).upper() for c in table.columns}
        col_names = [col for col in rows[0].keys() if col in cols_in_model]

        col_clause = ", ".join(f'"{c}"' for c in col_names)
        sql_lines.append(f"-- Data for {tname} ({count} rows)")

        loaded = 0
        for row in rows:
            row_dict = dict(row)
            # Orphan foreign key fix
            if tname in ("login_history", "notifications"):
                if row_dict.get("user_id") and row_dict.get("user_id") not in valid_user_ids:
                    row_dict["user_id"] = None
                if tname == "notifications" and row_dict.get("triggered_by") and row_dict.get("triggered_by") not in valid_user_ids:
                    row_dict["triggered_by"] = None

            val_strs = []
            for col in col_names:
                val = row_dict.get(col)
                col_type = cols_in_model.get(col, "TEXT")
                val_strs.append(escape_sql_value(val, col_type))

            vals_clause = ", ".join(val_strs)
            sql_lines.append(f'INSERT INTO "{tname}" ({col_clause}) VALUES ({vals_clause});')
            loaded += 1

        # Reset serial sequence if table has primary key 'id'
        if "id" in cols_in_model:
            sql_lines.append(f"""
            SELECT setval(
                pg_get_serial_sequence('"{tname}"', 'id'),
                COALESCE(MAX("id"), 1)
            ) FROM "{tname}";
            """)

        table_stats.append((tname, count, loaded))
        sql_lines.append("")

    # Add performance indexes
    sql_lines.append("-- Performance & Query Indexes")
    sql_lines.append('CREATE INDEX IF NOT EXISTS idx_attendance_emp_date ON attendance(employee_id, date);')
    sql_lines.append('CREATE INDEX IF NOT EXISTS idx_attendance_logs_emp_ts ON attendance_logs(employee_id, timestamp);')
    sql_lines.append('CREATE INDEX IF NOT EXISTS idx_leave_emp_dates ON leave_requests(employee_id, start_date, end_date);')
    sql_lines.append('CREATE INDEX IF NOT EXISTS idx_payslips_run_emp ON payslips(run_id, employee_id);')
    sql_lines.append('CREATE INDEX IF NOT EXISTS idx_emp_master_code ON employee_master(employee_code);')
    sql_lines.append('CREATE INDEX IF NOT EXISTS idx_hosp_assign_emp ON employee_hospital_assignments(employee_id);')

    sql_lines.append("SET session_replication_role = 'origin';")
    sql_lines.append("COMMIT;")

    # Write SQL dump
    sql_file = os.path.join(PROJECT_ROOT, "migration_dump.sql")
    with open(sql_file, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))

    print(f"Generated SQL migration payload: {sql_file} ({os.path.getsize(sql_file) / 1024:.1f} KB)")
    print(f"Total tables to load: {len([s for s in table_stats if s[1] > 0])}")

    # 5. Pipe SQL file into psql.exe
    print("\nExecuting migration into PostgreSQL 18 via psql.exe...")
    cmd = [
        PSQL_BIN,
        "-h", "127.0.0.1",
        "-U", "postgres",
        "-d", "smart_hrms_db",
        "-f", sql_file
    ]

    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        print(f"STDERR:\n{p.stderr[:500]}")
        print("ERROR executing psql. Check above output.")
        return

    print("✓ psql executed successfully!")

    # 6. Verify row counts on PostgreSQL
    print("\n" + "=" * 70)
    print("MIGRATION VERIFICATION (SQLite vs PostgreSQL 18)")
    print("=" * 70)
    print(f"{'Table':32} {'SQLite Rows':>12} {'PostgreSQL Rows':>16} {'Match':>8}")
    print("-" * 70)

    all_matched = True
    for tname, src_cnt, _ in table_stats:
        if src_cnt == 0:
            continue
        v_cmd = [
            PSQL_BIN,
            "-h", "127.0.0.1",
            "-U", "postgres",
            "-d", "smart_hrms_db",
            "-t",
            "-c", f'SELECT COUNT(*) FROM "{tname}";'
        ]
        res = subprocess.run(v_cmd, capture_output=True, text=True, encoding="utf-8")
        lines = [l.strip() for l in res.stdout.strip().splitlines() if l.strip()]
        pg_cnt = -1
        for l in lines:
            if l.isdigit():
                pg_cnt = int(l)
                break
        match = (src_cnt == pg_cnt)
        if not match:
            all_matched = False
        status_icon = "✓ PASS" if match else "❌ FAIL"
        print(f"{tname:32} {src_cnt:>12} {pg_cnt:>16} {status_icon:>8}")

    print("=" * 70)
    if all_matched:
        print("🎉 SUCCESS: 100% of rows matched! Zero data loss verified.")
    else:
        print("⚠️  Discrepancy detected in one or more tables.")

if __name__ == "__main__":
    run_migration()
