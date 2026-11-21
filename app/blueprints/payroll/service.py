"""blueprints/payroll/service.py"""

import json
import logging
from calendar import monthrange
from datetime import date, datetime, timezone
from typing import Optional, Tuple

from app.extensions.database import db
from app.models.payroll import PayrollRun, Payslip, SalaryStructure, EmployeeSalaryMaster
from app.models.attendance import Attendance
from app.models.employee import Employee
from sqlalchemy import extract

logger = logging.getLogger(__name__)


class PayrollService:

    def get_all_runs(self, page: int = 1, per_page: int = 20):
        return (PayrollRun.query.filter_by(is_deleted=False)
                .order_by(PayrollRun.year.desc(), PayrollRun.month.desc())
                .paginate(page=page, per_page=per_page, error_out=False))

    def get_run(self, run_id: int) -> Optional[PayrollRun]:
        return PayrollRun.query.filter_by(id=run_id, is_deleted=False).first()

    def get_run_or_404(self, run_id: int) -> PayrollRun:
        from flask import abort
        r = self.get_run(run_id)
        if not r:
            abort(404)
        return r

    def get_payslips_for_run(self, run_id: int) -> list:
        return Payslip.query.filter_by(run_id=run_id, is_deleted=False).all()

    def get_employee_payslips(self, employee_id: int, page: int = 1, per_page: int = 20):
        return (Payslip.query.filter_by(employee_id=employee_id, is_deleted=False)
                .join(PayrollRun, Payslip.run_id == PayrollRun.id)
                .order_by(PayrollRun.year.desc(), PayrollRun.month.desc())
                .paginate(page=page, per_page=per_page, error_out=False))

    def get_salary_structures(self) -> list:
        return SalaryStructure.query.filter_by(is_deleted=False, is_active=True).all()

    def create_run(self, month: int, year: int, created_by: int) -> Tuple[bool, str, Optional[PayrollRun]]:
        import calendar
        existing = PayrollRun.query.filter_by(month=month, year=year, is_deleted=False).first()
        if existing:
            return False, f"Payroll run for {calendar.month_name[month]} {year} already exists.", None
        label = f"{calendar.month_name[month]} {year}"
        run = PayrollRun(month=month, year=year, period_label=label,
                         status="draft", created_by=created_by)
        db.session.add(run)
        db.session.commit()
        return True, f"Payroll run created for {label}.", run

    def process_run(self, run_id: int, processed_by: int) -> Tuple[bool, str]:
        """
        Auto-calculate payslips for all employees based on attendance.
        Uses a flat salary model (basic salary per day * days present).
        """
        run = self.get_run(run_id)
        if not run:
            return False, "Payroll run not found."
        if run.status not in ("draft", "processing", "processed"):
            return False, f"Cannot process a run with status '{run.status}' (must be draft or processed)."

        run.status = "processing"
        db.session.commit()

        employees = Employee.query.filter_by(is_deleted=False).all()
        _, days_in_month = monthrange(run.year, run.month)
        total_gross = 0.0
        total_net   = 0.0
        count       = 0

        for emp in employees:
            # Count attendance days
            att_records = Attendance.query.filter(
                Attendance.employee_id == emp.id,
                extract("year",  Attendance.date) == run.year,
                extract("month", Attendance.date) == run.month,
                Attendance.is_deleted == False,
            ).all()

            days_present = sum(1 for a in att_records if a.status == "present")
            leave_days   = sum(1 for a in att_records if a.status == "on_leave")
            half_days    = sum(0.5 for a in att_records if (a.status == "half_day" or getattr(a, "is_half_day", False)))

            # 3 Late Marks Policy (Per-Month Reset):
            # 20-min grace buffer. After every 3 late marks in THIS calendar month, 1 half-day deduction is applied.
            # In the next month, the counter resets back to 0.
            late_count = sum(1 for a in att_records if getattr(a, "is_late", False))
            late_deduction_days = (late_count // 3) * 0.5

            payable_days = max(0.0, days_present + half_days + leave_days - late_deduction_days)
            days_absent  = max(0.0, days_in_month - (days_present + half_days + leave_days))

            # Look up employee's imported salary structure master
            salary_master = EmployeeSalaryMaster.query.filter_by(
                employee_code=emp.employee_code, is_active=True
            ).first()

            payable_days = days_present + leave_days

            if salary_master:
                # Use real configured salary and deductions from imported Excel
                monthly_gross = float(salary_master.salary_amount)
                daily_rate    = monthly_gross / days_in_month if days_in_month > 0 else monthly_gross
                earned_gross  = round(daily_rate * payable_days, 2)

                # Deductions
                # Pro-rate PF with attendance days if absent, or use full amount if present
                att_ratio = (payable_days / days_in_month) if days_in_month > 0 else 1.0
                pf_deduction = round(float(salary_master.pf_amount) * att_ratio, 2)
                tds_deduction = round(float(salary_master.tds_amount), 2)
                pt_deduction = round(float(salary_master.pt_amount), 2)

                total_ded = round(pf_deduction + tds_deduction + pt_deduction, 2)
                net = max(0.0, round(earned_gross - total_ded, 2))

                earned_basic = earned_gross
                gross = earned_gross

                earn_dict = {
                    "Monthly CTC / Gross": round(monthly_gross, 2),
                    "Payable Days": f"{payable_days} / {days_in_month} Days",
                    "Earned Gross": round(earned_gross, 2),
                }
                ded_dict = {}
                if pf_deduction > 0:
                    ded_dict["Provident Fund (PF)"] = round(pf_deduction, 2)
                if tds_deduction > 0:
                    ded_dict["Tax Deducted at Source (TDS)"] = round(tds_deduction, 2)
                if pt_deduction > 0:
                    ded_dict["Professional Tax (PT)"] = round(pt_deduction, 2)

                earnings   = json.dumps(earn_dict)
                deductions = json.dumps(ded_dict)
            else:
                # ZERO DUMMY DATA: If salary master has not been uploaded yet, do not fabricate numbers
                basic         = 0.0
                daily_rate    = 0.0
                earned_basic  = 0.0
                hra           = 0.0
                conveyance    = 0.0
                gross         = 0.0

                pf_deduction  = 0.0
                tds_deduction = 0.0
                pt_deduction  = 0.0
                total_ded     = 0.0
                net           = 0.0

                earnings   = json.dumps({"Notice": "Salary master pending upload by HR", "Basic": 0.0})
                deductions = json.dumps({})

            # Remove old payslip for this emp+run if exists
            old = Payslip.query.filter_by(run_id=run.id, employee_id=emp.id).first()
            if old:
                db.session.delete(old)

            slip = Payslip(
                run_id=run.id, employee_id=emp.id,
                basic_salary=round(earned_basic, 2),
                gross_salary=round(gross, 2),
                total_deductions=round(total_ded, 2),
                net_salary=round(net, 2),
                working_days=days_in_month,
                days_present=days_present,
                days_absent=max(0, days_absent),
                leave_days=leave_days,
                earnings_breakdown=earnings,
                deductions_breakdown=deductions,
                status="draft",
                created_by=processed_by,
            )
            db.session.add(slip)
            total_gross += gross
            total_net   += net
            count       += 1

        run.status         = "processed"
        run.total_gross    = round(total_gross, 2)
        run.total_net      = round(total_net, 2)
        run.total_deductions = round(total_gross - total_net, 2)
        run.employee_count = count
        db.session.commit()
        logger.info("PAYROLL_PROCESSED | run_id=%s | employees=%s | total_net=%.2f", run.id, count, total_net)
        return True, f"Payroll processed for {count} employees. Total Net: ₹{total_net:,.2f}"

    def approve_run(self, run_id: int, approved_by: int) -> Tuple[bool, str]:
        run = self.get_run(run_id)
        if not run:
            return False, "Run not found."
        if run.status != "processed":
            return False, "Only processed runs can be approved."
        run.status      = "approved"
        run.approved_by = approved_by
        run.approved_on = datetime.utcnow()
        db.session.commit()
        return True, "Payroll run approved."

    def mark_paid(self, run_id: int) -> Tuple[bool, str]:
        run = self.get_run(run_id)
        if not run:
            return False, "Run not found."
        if run.status != "approved":
            return False, "Only approved runs can be marked as paid."
        run.status = "paid"
        Payslip.query.filter_by(run_id=run.id).update({"status": "paid"})
        db.session.commit()
        return True, "Payroll marked as paid."
