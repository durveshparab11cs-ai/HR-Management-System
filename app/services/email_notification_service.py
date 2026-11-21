"""
app/services/email_notification_service.py
=========================================
Centralized Email Notification Service for CS Creative Solutions HRMS.
Sender address: executivehr0001@gmail.com

Features:
1. 20-minute buffer enforcement & Late Mark Warnings (Warning 1, Warning 2, Half-Day Penalty on 3rd).
2. Leave Request dispatch to Reporting Manager with single-click Email Actions (Approve / Reject).
3. Bidirectional Synchronization: Actions taken via email or portal automatically update both channels.
4. Fail-safe delivery: Logs all outgoing emails cleanly; never halts application execution.
"""

import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional

from flask import current_app, render_template_string, url_for
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer

from app.extensions.database import db
from app.extensions.mail import mail
from app.models.notification import Notification

logger = logging.getLogger(__name__)

DEFAULT_SENDER = "CS Creative Solutions HR <executivehr0001@gmail.com>"
HR_MAILBOX = "executivehr0001@gmail.com"


# ══════════════════════════════════════════════════════════════════════════════
# 1. TOKEN ENGINE (Single-Click Email Actions)
# ══════════════════════════════════════════════════════════════════════════════

def generate_leave_action_token(request_id: int, request_type: str, manager_code: str) -> str:
    """Generate a secure, signed URL-safe token for email approval/rejection."""
    secret = current_app.config.get("SECRET_KEY", "hrms-secure-salt-2026")
    serializer = URLSafeTimedSerializer(secret, salt="leave-email-action-v1")
    return serializer.dumps({
        "req_id": request_id,
        "req_type": request_type,
        "mgr_code": manager_code.strip().upper(),
        "created_at": datetime.utcnow().isoformat(),
    })


def verify_leave_action_token(token: str, max_age_seconds: int = 604800) -> Optional[dict]:
    """Verify and decode a leave action token (valid for 7 days)."""
    secret = current_app.config.get("SECRET_KEY", "hrms-secure-salt-2026")
    serializer = URLSafeTimedSerializer(secret, salt="leave-email-action-v1")
    try:
        data = serializer.loads(token, max_age=max_age_seconds)
        return data
    except Exception as exc:
        logger.warning("Token verification failed: %s", exc)
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 2. CORE DISPATCHER
# ══════════════════════════════════════════════════════════════════════════════

def _deliver_email_async(app, msg: Message):
    """Deliver an email in a background thread with fail-safe exception logging."""
    with app.app_context():
        try:
            mail.send(msg)
            logger.info("EMAIL_DELIVERED | To=%s | Subject=%s", msg.recipients, msg.subject)
        except Exception as exc:
            # Catch SMTP authentication / network errors gracefully
            logger.warning(
                "EMAIL_SEND_SUPPRESSED_OR_FAILED | To=%s | Subject=%s | Reason=%s",
                msg.recipients, msg.subject, exc
            )


def dispatch_html_email(
    subject: str,
    recipients: list[str],
    html_content: str,
    text_content: Optional[str] = None,
    cc: Optional[list[str]] = None,
    async_send: bool = True
) -> bool:
    """Dispatch an HTML email with CS Creative Solutions branding."""
    if not recipients:
        return False

    app = current_app._get_current_object()
    sender = app.config.get("MAIL_DEFAULT_SENDER") or DEFAULT_SENDER

    msg = Message(
        subject=subject,
        recipients=recipients,
        html=html_content,
        body=text_content or "Please view this message in an HTML-compatible email client.",
        sender=sender,
        cc=cc,
    )

    if async_send:
        threading.Thread(target=_deliver_email_async, args=(app, msg), daemon=True).start()
    else:
        _deliver_email_async(app, msg)

    return True


# ══════════════════════════════════════════════════════════════════════════════
# 3. LATE MARK WARNING & HALF-DAY NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════════════

def send_late_warning_notification(
    employee,
    attendance,
    late_count: int,
    late_minutes: int,
    punch_time_str: str,
    shift_start_str: str = "09:00 AM",
    reporting_manager_email: Optional[str] = None,
    async_send: bool = True,
) -> bool:
    """
    Send late mark warning emails to the employee and notify HR/Reporting Manager.
    Policy: 20 mins grace buffer. 3 late marks = 1 Half Day deduction.
    """
    emp_name = getattr(employee, "full_name", f"Employee #{employee.id}")
    emp_code = getattr(employee, "employee_code", f"E-{employee.id}")
    emp_dept = getattr(employee, "department", "General")
    
    # Resolve employee recipient email
    emp_email = getattr(employee, "personal_email", None)
    if not emp_email and hasattr(employee, "user") and employee.user:
        emp_email = employee.user.email
    if not emp_email or "@hrms.internal" in emp_email:
        # Fallback to test/HR mailbox
        emp_email = HR_MAILBOX

    # Determine warning tier
    cycle_index = late_count % 3
    if cycle_index == 1:
        tier = "warning_1"
        badge_text = "WARNING 1 OF 3"
        badge_color = "#f59e0b"
        badge_bg = "#fef3c7"
        headline = "Late Arrival Recorded — Warning 1 of 3"
        summary_msg = (
            f"You have accumulated <strong>1 late arrival mark</strong> this month. "
            f"You have <strong>2 warnings remaining</strong> before an automatic Half-Day deduction is applied."
        )
        subject = f"Notice: Late Arrival Warning (1/3) — {emp_name} ({emp_code})"
    elif cycle_index == 2:
        tier = "warning_2"
        badge_text = "URGENT • FINAL WARNING (2 OF 3)"
        badge_color = "#ea580c"
        badge_bg = "#ffedd5"
        headline = "Late Arrival Warning — 2nd Mark (Final Warning)"
        summary_msg = (
            f"You have accumulated <strong>2 late arrival marks</strong> this month. "
            f"<strong style='color:#ea580c;'>FINAL WARNING:</strong> Your next late arrival this month will "
            f"automatically result in a <strong>0.5-Day salary deduction</strong>."
        )
        subject = f"URGENT: Late Arrival Warning (2/3) — {emp_name} ({emp_code})"
    else:
        tier = "penalty_half_day"
        badge_text = "POLICY ACTION • HALF-DAY DEDUCTION APPLIED"
        badge_color = "#dc2626"
        badge_bg = "#fee2e2"
        headline = "3rd Late Mark Applied — Half-Day Deduction Enforced"
        summary_msg = (
            f"You have recorded your <strong>3rd late arrival</strong> for the current month. "
            f"As per company attendance policy (3 late marks = 1 half-day penalty), "
            f"your attendance for today has been recorded as <strong style='color:#dc2626;'>HALF DAY</strong>."
        )
        subject = f"Policy Action: 3rd Late Mark — Half-Day Deduction Applied ({emp_code})"

    date_str = attendance.date.strftime("%A, %d %B %Y") if hasattr(attendance, "date") else datetime.now().strftime("%d %B %Y")

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif; background-color:#f1f5f9; margin:0; padding:24px; color:#0f172a;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:600px; background-color:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 10px 25px rgba(0,0,0,0.06); border:1px solid #e2e8f0;">
        <!-- Header Banner -->
        <tr>
          <td style="padding:28px 32px; background:linear-gradient(135deg, #0284c7 0%, #2563eb 100%); color:#ffffff;">
            <div style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; opacity:0.85; margin-bottom:4px;">CS Creative Solutions &bull; Attendance Governance</div>
            <div style="font-size:22px; font-weight:800; line-height:1.2;">Attendance Warning Notice</div>
          </td>
        </tr>

        <!-- Status Badge -->
        <tr>
          <td style="padding:24px 32px 12px 32px;">
            <span style="display:inline-block; padding:6px 14px; border-radius:9999px; font-size:12px; font-weight:700; color:{badge_color}; background-color:{badge_bg}; border:1px solid {badge_color}33;">
              {badge_text}
            </span>
            <h2 style="font-size:18px; font-weight:700; color:#0f172a; margin:14px 0 8px 0;">{headline}</h2>
            <p style="font-size:14px; line-height:1.6; color:#475569; margin:0;">
              Dear <strong>{emp_name}</strong> ({emp_code}),<br>
              {summary_msg}
            </p>
          </td>
        </tr>

        <!-- Details Card -->
        <tr>
          <td style="padding:12px 32px 24px 32px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:16px;">
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600;">Date of Punch</td>
                <td style="padding:8px 12px; font-size:13px; color:#0f172a; font-weight:700; text-align:right;">{date_str}</td>
              </tr>
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Punch Time</td>
                <td style="padding:8px 12px; font-size:13px; color:#0f172a; font-weight:700; text-align:right; border-top:1px solid #e2e8f0;">{punch_time_str} IST</td>
              </tr>
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Shift In-Time</td>
                <td style="padding:8px 12px; font-size:13px; color:#0f172a; font-weight:700; text-align:right; border-top:1px solid #e2e8f0;">{shift_start_str}</td>
              </tr>
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Company Buffer</td>
                <td style="padding:8px 12px; font-size:13px; color:#059669; font-weight:700; text-align:right; border-top:1px solid #e2e8f0;">20 Minutes Grace Time</td>
              </tr>
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Late Minutes Past Buffer</td>
                <td style="padding:8px 12px; font-size:13px; color:#dc2626; font-weight:800; text-align:right; border-top:1px solid #e2e8f0;">+{late_minutes} min late</td>
              </tr>
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Monthly Late Count</td>
                <td style="padding:8px 12px; font-size:13px; color:#0284c7; font-weight:800; text-align:right; border-top:1px solid #e2e8f0;">{late_count} Late Mark(s) this month</td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Policy Explainer -->
        <tr>
          <td style="padding:0 32px 28px 32px;">
            <div style="background-color:#eff6ff; border-left:4px solid #0284c7; border-radius:6px; padding:12px 16px; font-size:13px; color:#1e3a8a; line-height:1.5;">
              <strong>Company Attendance Policy Reminder:</strong><br>
              Every personnel is granted a <strong>20-minute grace buffer</strong> past scheduled shift start. 
              After 3 late marks within a single calendar month, an automated Half-Day deduction is recorded on payroll.
            </div>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:20px 32px; background-color:#f8fafc; border-top:1px solid #e2e8f0; font-size:12px; color:#94a3b8; text-align:center;">
            CS Creative Solutions &bull; Executive HR &bull; Mail: executivehr0001@gmail.com<br>
            Automated notification generated by Smart HRMS Enterprise Platform.
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    recipients = [emp_email]
    cc = [HR_MAILBOX]
    if reporting_manager_email and reporting_manager_email not in recipients:
        cc.append(reporting_manager_email)

    # In-app notification
    try:
        user_id = getattr(employee, "user_id", None)
        if user_id:
            notif = Notification(
                user_id=user_id,
                title=f"Late Mark Notice ({badge_text})",
                message=f"Late check-in recorded today ({punch_time_str}). Late count: {late_count} this month.",
                category="warning" if cycle_index != 0 else "danger",
            )
            db.session.add(notif)
            db.session.commit()
    except Exception as exc:
        logger.warning("Failed to store in-app notification: %s", exc)

    return dispatch_html_email(subject, recipients, html_body, cc=cc, async_send=async_send)


# ══════════════════════════════════════════════════════════════════════════════
# 4. LEAVE REQUEST NOTIFICATION TO REPORTING MANAGER (BIDIRECTIONAL ACTIONS)
# ══════════════════════════════════════════════════════════════════════════════

def send_leave_request_to_manager(
    leave_req,
    employee,
    manager_name: str,
    manager_email: Optional[str] = None,
    request_type: str = "leave",
    base_url: Optional[str] = None,
    async_send: bool = True,
) -> bool:
    """
    Send leave request to Reporting Manager with Single-Click Approve/Reject links.
    Bidirectional: clicking in email immediately updates HRMS portal, and vice versa.
    """
    emp_name = getattr(employee, "full_name", f"Employee #{employee.id}")
    emp_code = getattr(employee, "employee_code", f"E-{employee.id}")
    emp_dept = getattr(employee, "department", "General")
    emp_location = getattr(employee, "branch", "Hospital Site")

    # Leave dates formatting
    if request_type == "leave":
        start_str = leave_req.start_date.strftime("%d %b %Y")
        end_str = leave_req.end_date.strftime("%d %b %Y")
        total_days_str = f"{leave_req.total_days} Day(s)"
        type_name = getattr(leave_req.leave_type, "name", "Leave") if hasattr(leave_req, "leave_type") else "General Leave"
        reason_str = leave_req.reason or "No specific reason provided."
    elif request_type == "half_day":
        start_str = leave_req.date.strftime("%d %b %Y")
        end_str = start_str
        total_days_str = f"0.5 Day ({leave_req.half_type.replace('_', ' ').title()})"
        type_name = "Half Day Leave"
        reason_str = leave_req.reason or "No specific reason provided."
    else:  # early_leave
        start_str = leave_req.date.strftime("%d %b %Y")
        end_str = start_str
        total_days_str = f"Early Leave ({leave_req.expected_time.strftime('%I:%M %p') if getattr(leave_req, 'expected_time', None) else 'Scheduled'})"
        type_name = "Early Leave Request"
        reason_str = leave_req.reason or "No specific reason provided."

    comp_off_row = ""
    if request_type == "leave" and getattr(leave_req, "comp_off_work_date", None):
        co_date_str = leave_req.comp_off_work_date.strftime("%d %b %Y (%A)")
        comp_off_row = f"""
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Sunday / Holiday Worked</td>
                <td style="padding:8px 12px; font-size:13px; color:#7c3aed; font-weight:800; text-align:right; border-top:1px solid #e2e8f0;">{co_date_str}</td>
              </tr>
        """

    # Generate single-click signed tokens
    mgr_code = getattr(leave_req, "reporting_manager_code", "MANAGER")
    token_approve = generate_leave_action_token(leave_req.id, request_type, mgr_code)
    token_reject = generate_leave_action_token(leave_req.id, request_type, mgr_code)

    # Build actionable URLs
    root = (base_url or "http://localhost:8000").rstrip("/")
    approve_url = f"{root}/leave/email-action?token={token_approve}&action=approve"
    reject_url = f"{root}/leave/email-action?token={token_reject}&action=reject"
    portal_url = f"{root}/leave/manager/requests"

    target_email = manager_email
    if not target_email or "@hrms.internal" in target_email:
        target_email = HR_MAILBOX

    subject = f"Action Required: {type_name} Request from {emp_name} ({emp_code})"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif; background-color:#f1f5f9; margin:0; padding:24px; color:#0f172a;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px; background-color:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 10px 25px rgba(0,0,0,0.06); border:1px solid #e2e8f0;">
        <!-- Header -->
        <tr>
          <td style="padding:28px 32px; background:linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color:#ffffff;">
            <div style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; opacity:0.85; margin-bottom:4px;">CS Creative Solutions &bull; Leave Authorization</div>
            <div style="font-size:22px; font-weight:800; line-height:1.2;">New {type_name} Awaiting Your Approval</div>
          </td>
        </tr>

        <!-- Salutation -->
        <tr>
          <td style="padding:24px 32px 12px 32px;">
            <p style="font-size:14px; line-height:1.6; color:#475569; margin:0;">
              Dear <strong>{manager_name}</strong>,<br>
              An employee under your reporting structure has submitted a new <strong>{type_name}</strong> request through the Smart HRMS portal. 
              Please review the particulars below and submit your decision.
            </p>
          </td>
        </tr>

        <!-- Details Card -->
        <tr>
          <td style="padding:12px 32px 20px 32px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:16px;">
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600;">Employee Name</td>
                <td style="padding:8px 12px; font-size:13px; color:#0f172a; font-weight:700; text-align:right;">{emp_name}</td>
              </tr>
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Employee Code</td>
                <td style="padding:8px 12px; font-size:13px; color:#0284c7; font-weight:700; text-align:right; font-family:monospace; border-top:1px solid #e2e8f0;">{emp_code}</td>
              </tr>
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Department / Site</td>
                <td style="padding:8px 12px; font-size:13px; color:#0f172a; font-weight:600; text-align:right; border-top:1px solid #e2e8f0;">{emp_dept} &bull; {emp_location}</td>
              </tr>
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Leave Category</td>
                <td style="padding:8px 12px; font-size:13px; color:#7c3aed; font-weight:700; text-align:right; border-top:1px solid #e2e8f0;">{type_name}</td>
              </tr>
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Period / Dates</td>
                <td style="padding:8px 12px; font-size:13px; color:#0f172a; font-weight:700; text-align:right; border-top:1px solid #e2e8f0;">{start_str} to {end_str} ({total_days_str})</td>
              </tr>
              {comp_off_row}
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Reason Provided</td>
                <td style="padding:8px 12px; font-size:13px; color:#334155; font-style:italic; text-align:right; border-top:1px solid #e2e8f0;">&ldquo;{reason_str}&rdquo;</td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- One-Click Decision Buttons -->
        <tr>
          <td style="padding:10px 32px 28px 32px; text-align:center;">
            <div style="font-size:13px; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:14px;">Instant One-Click Decision</div>
            <table align="center" border="0" cellpadding="0" cellspacing="0">
              <tr>
                <td style="padding-right:12px;">
                  <a href="{approve_url}" style="display:inline-block; background-color:#059669; color:#ffffff; font-size:14px; font-weight:700; text-decoration:none; padding:12px 28px; border-radius:10px; box-shadow:0 4px 12px rgba(5,150,105,0.3);">
                    &check; Approve Leave
                  </a>
                </td>
                <td style="padding-left:12px;">
                  <a href="{reject_url}" style="display:inline-block; background-color:#dc2626; color:#ffffff; font-size:14px; font-weight:700; text-decoration:none; padding:12px 28px; border-radius:10px; box-shadow:0 4px 12px rgba(220,38,38,0.3);">
                    &cross; Reject Leave
                  </a>
                </td>
              </tr>
            </table>
            <div style="margin-top:18px;">
              <a href="{portal_url}" style="font-size:12px; color:#0284c7; text-decoration:underline;">Or review all pending approvals in the HRMS Portal</a>
            </div>
          </td>
        </tr>

        <!-- Sync Notice -->
        <tr>
          <td style="padding:0 32px 24px 32px;">
            <div style="background-color:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px 14px; font-size:12px; color:#64748b; text-align:center;">
              <strong>Automatic Synchronization:</strong> Deciding via this email or directly in the portal updates both channels automatically in real-time.
            </div>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:20px 32px; background-color:#f8fafc; border-top:1px solid #e2e8f0; font-size:12px; color:#94a3b8; text-align:center;">
            CS Creative Solutions &bull; Executive HR &bull; Mail: executivehr0001@gmail.com
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    recipients = [target_email]
    cc = [HR_MAILBOX]

    return dispatch_html_email(subject, recipients, html_body, cc=cc, async_send=async_send)


def send_leave_submission_to_employee(
    leave_req,
    employee,
    manager_name: str,
    request_type: str = "leave",
) -> bool:
    """Send submission acknowledgment email to the applicant employee."""
    emp_name = getattr(employee, "full_name", f"Employee #{employee.id}")
    emp_code = getattr(employee, "employee_code", f"E-{employee.id}")

    emp_email = getattr(employee, "personal_email", None)
    if not emp_email and hasattr(employee, "user") and employee.user:
        emp_email = employee.user.email
    if not emp_email or "@hrms.internal" in emp_email:
        emp_email = HR_MAILBOX

    if request_type == "leave":
        start_str = leave_req.start_date.strftime("%d %b %Y")
        end_str = leave_req.end_date.strftime("%d %b %Y")
        total_days_str = f"{leave_req.total_days} Day(s)"
        type_name = getattr(leave_req.leave_type, "name", "Leave") if hasattr(leave_req, "leave_type") else "General Leave"
    elif request_type == "half_day":
        start_str = leave_req.date.strftime("%d %b %Y")
        end_str = start_str
        total_days_str = f"0.5 Day ({leave_req.half_type.replace('_', ' ').title()})"
        type_name = "Half Day Leave"
    else:
        start_str = leave_req.date.strftime("%d %b %Y")
        end_str = start_str
        total_days_str = "Early Leave"
        type_name = "Early Leave Request"

    subject = f"Leave Request Submitted: Awaiting Approval from {manager_name}"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif; background-color:#f1f5f9; margin:0; padding:24px; color:#0f172a;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:600px; background-color:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 10px 25px rgba(0,0,0,0.06); border:1px solid #e2e8f0;">
        <tr>
          <td style="padding:24px 32px; background:linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color:#ffffff;">
            <div style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; opacity:0.85;">CS Creative Solutions &bull; Leave Submission</div>
            <div style="font-size:20px; font-weight:800; line-height:1.2; margin-top:4px;">Request Forwarded to Reporting Manager</div>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px 12px 32px;">
            <p style="font-size:14px; line-height:1.6; color:#475569; margin:0;">
              Dear <strong>{emp_name}</strong> ({emp_code}),<br>
              Your <strong>{type_name}</strong> request has been successfully submitted and forwarded to your reporting manager, <strong>{manager_name}</strong>, for approval.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:12px 32px 20px 32px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:16px;">
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600;">Category</td>
                <td style="padding:8px 12px; font-size:13px; color:#0f172a; font-weight:700; text-align:right;">{type_name}</td>
              </tr>
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Dates</td>
                <td style="padding:8px 12px; font-size:13px; color:#0f172a; font-weight:700; text-align:right; border-top:1px solid #e2e8f0;">{start_str} to {end_str} ({total_days_str})</td>
              </tr>
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Reporting Manager</td>
                <td style="padding:8px 12px; font-size:13px; color:#0284c7; font-weight:700; text-align:right; border-top:1px solid #e2e8f0;">{manager_name}</td>
              </tr>
              <tr>
                <td style="padding:8px 12px; font-size:13px; color:#64748b; font-weight:600; border-top:1px solid #e2e8f0;">Current Status</td>
                <td style="padding:8px 12px; font-size:13px; color:#f59e0b; font-weight:800; text-align:right; border-top:1px solid #e2e8f0;">PENDING APPROVAL</td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:0 32px 24px 32px; font-size:13px; color:#64748b; line-height:1.5;">
            You will receive an update notification as soon as your reporting manager submits their decision.
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px; background-color:#f8fafc; border-top:1px solid #e2e8f0; font-size:12px; color:#94a3b8; text-align:center;">
            CS Creative Solutions &bull; Executive HR &bull; Mail: executivehr0001@gmail.com
          </td>
        </tr>
      </table>
    </body>
    </html>
    """
    return dispatch_html_email(subject, [emp_email], html_body, cc=[HR_MAILBOX])


def send_leave_decision_to_employee(
    leave_req,
    employee,
    action: str,  # 'approved' or 'rejected'
    reviewer_name: str,
    comment: str = "",
    request_type: str = "leave",
) -> bool:
    """Send confirmation email to employee after leave request is approved/rejected."""
    emp_name = getattr(employee, "full_name", f"Employee #{employee.id}")
    emp_code = getattr(employee, "employee_code", f"E-{employee.id}")
    
    emp_email = getattr(employee, "personal_email", None)
    if not emp_email and hasattr(employee, "user") and employee.user:
        emp_email = employee.user.email
    if not emp_email or "@hrms.internal" in emp_email:
        emp_email = HR_MAILBOX

    is_approved = (action == "approved")
    badge_text = "APPROVED" if is_approved else "REJECTED"
    badge_color = "#059669" if is_approved else "#dc2626"
    badge_bg = "#ecfdf5" if is_approved else "#fee2e2"
    
    type_name = "Leave Request" if request_type == "leave" else ("Half Day Request" if request_type == "half_day" else "Early Leave Request")
    subject = f"Update: Your {type_name} has been {action.upper()} — CS Creative Solutions"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif; background-color:#f1f5f9; margin:0; padding:24px; color:#0f172a;">
      <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:580px; background-color:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 10px 25px rgba(0,0,0,0.06); border:1px solid #e2e8f0;">
        <tr>
          <td style="padding:24px 32px; background:linear-gradient(135deg, {'#059669' if is_approved else '#dc2626'} 0%, {'#047857' if is_approved else '#b91c1c'} 100%); color:#ffffff;">
            <div style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; opacity:0.85;">CS Creative Solutions &bull; Leave Status</div>
            <div style="font-size:20px; font-weight:800; line-height:1.2; margin-top:4px;">{type_name} {action.title()}</div>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px;">
            <span style="display:inline-block; padding:4px 12px; border-radius:9999px; font-size:12px; font-weight:700; color:{badge_color}; background-color:{badge_bg}; border:1px solid {badge_color}33;">
              {badge_text}
            </span>
            <p style="font-size:14px; line-height:1.6; color:#475569; margin:16px 0 0 0;">
              Dear <strong>{emp_name}</strong> ({emp_code}),<br>
              Your <strong>{type_name}</strong> has been <strong>{action}</strong> by <strong>{reviewer_name}</strong>.
              {'<br><br>Reason/Note: <em>' + comment + '</em>' if comment else ''}
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px; background-color:#f8fafc; border-top:1px solid #e2e8f0; font-size:12px; color:#94a3b8; text-align:center;">
            CS Creative Solutions &bull; Executive HR &bull; Mail: executivehr0001@gmail.com
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    return dispatch_html_email(subject, [emp_email], html_body, cc=[HR_MAILBOX])
