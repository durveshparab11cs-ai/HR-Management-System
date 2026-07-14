"""blueprints/payroll/service.py"""

import json
import logging
from calendar import monthrange
from datetime import date, datetime, timezone
from typing import Optional, Tuple

from app.extensions.database import db
from app.models.payroll import PayrollRun, Payslip, SalaryStructure
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
        if run.status not in ("draft", "processing"):
            return False, f"Cannot process a run with status '{run.status}'."

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
            days_absent  = days_in_month - days_present - leave_days

            # Placeholder salary — replace with actual structure when HR configures it
            basic         = 30000.0
            daily_rate    = basic / days_in_month
            earned_basic  = daily_rate * (days_present + leave_days)
            hra           = earned_basic * 0.4
            conveyance    = 1600.0
            gross         = earned_basic + hra + conveyance

            pf_deduction  = earned_basic * 0.12
            pt_deduction  = 200.0
            net           = gross - pf_deduction - pt_deduction

            earnings   = json.dumps({"Basic": round(earned_basic,2), "HRA": round(hra,2), "Conveyance": conveyance})
            deductions = json.dumps({"PF (12%)": round(pf_deduction,2), "Professional Tax": pt_deduction})

            # Remove old payslip for this emp+run if exists
            old = Payslip.query.filter_by(run_id=run.id, employee_id=emp.id).first()
            if old:
                db.session.delete(old)

            slip = Payslip(
                run_id=run.id, employee_id=emp.id,
                basic_salary=round(earned_basic, 2),
                gross_salary=round(gross, 2),
                total_deductions=round(pf_deduction + pt_deduction, 2),
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
        run.approved_on = datetime.now(timezone.utc)
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
