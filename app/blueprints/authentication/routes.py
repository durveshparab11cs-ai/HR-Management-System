"""
blueprints/authentication/routes.py
=====================================
Authentication routes — Employee Code-based login and registration.
"""

from flask import current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user

from app.constants.limits import Limits
from app.constants.enums import DEPARTMENT_CHOICES
from app.extensions.limiter import limiter
from app.blueprints.employees.repository import EmployeeRepository
from .forms import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm
from .service import AuthService
from . import authentication_bp

_svc = AuthService()
_emp_repo = EmployeeRepository()


# ── Login / Register ──────────────────────────────────────────────────


@authentication_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_svc.get_dashboard_url(current_user))

    login_form    = LoginForm()
    register_form = RegisterForm()
    forgot_form   = ForgotPasswordForm()
    error         = None
    active_tab    = request.args.get("tab", "login")
    success_msg   = None

    if request.method == "POST":
        action = request.form.get("action", "login")

        if action == "login":
            if login_form.validate_on_submit():
                success, message, user = _svc.attempt_login(
                    employee_code=login_form.employee_code.data,
                    password=login_form.password.data,
                    department=login_form.department.data,
                    remember=login_form.remember_me.data,
                )
                if success:
                    next_url = request.args.get("next")
                    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                        return redirect(next_url)
                    return redirect(_svc.get_dashboard_url(user))
                error      = message
                active_tab = "login"
            else:
                first_err = next((errs[0] for field, errs in login_form.errors.items() if errs and field != 'csrf_token'), None)
                if not first_err and 'csrf_token' in login_form.errors:
                    first_err = "Session expired or invalid security token. Please refresh the page and try again."
                error      = first_err or "Please check your inputs and try again."
                active_tab = "login"

        elif action == "register":
            if register_form.validate_on_submit():
                ok, msg, user = _svc.register_by_code(
                    employee_code=register_form.employee_code.data,
                    password=register_form.password.data,
                    department=register_form.department.data or request.form.get("department", ""),
                    designation=register_form.designation.data or request.form.get("designation", ""),
                    working_location=request.form.get("working_location", "").strip(),
                    date_of_joining=request.form.get("date_of_joining", "").strip(),
                    email=request.form.get("email", "").strip(),
                )
                if ok:
                    flash(msg, "success")
                    return redirect(url_for("authentication.login") + "?tab=login")
                error      = msg
                active_tab = "register"
            else:
                first_err = next(iter(register_form.errors.values()))[0] if register_form.errors else None
                error      = first_err or "Please check your inputs and try again."
                active_tab = "register"

        elif action == "forgot":
            if forgot_form.validate_on_submit():
                ok, payload = _svc.initiate_password_reset(forgot_form.employee_code.data)
                if ok:
                    # Redirect directly to reset password page with token
                    return redirect(url_for("authentication.reset_password", token=payload))
                else:
                    error = payload
                    active_tab = "forgot"
            else:
                error = "Please enter a valid Employee Code."
                active_tab = "forgot"

    # Fetch available locations (Head Office + active hospitals)
    location_choices = ["Head Office"]
    try:
        from app.models.hospital import Hospital
        hosp_list = [h.hospital_name for h in Hospital.query.filter_by(is_active=True).order_by(Hospital.hospital_name).all()]
        location_choices += [h for h in hosp_list if h != "Head Office"]
    except Exception:
        pass

    return render_template(
        "authentication/login.html",
        title="Sign In",
        login_form=login_form,
        register_form=register_form,
        forgot_form=forgot_form,
        error=error,
        success_msg=success_msg,
        active_tab=active_tab,
        department_choices=DEPARTMENT_CHOICES,
        location_choices=location_choices,
    )


# ── AJAX: look up employee name from master ────────────────────────────

@authentication_bp.route("/lookup-employee")
def lookup_employee():
    """
    AJAX endpoint called by the registration form to fetch employee name.
    GET /auth/lookup-employee?code=E-2603028
    Returns JSON {found, name, department, designation, message}
    """
    code = request.args.get("code", "").strip().upper()
    if not code:
        return jsonify(found=False, message="Enter an Employee Code.")

    found, message, data = _svc.lookup_employee(code)
    if found:
        return jsonify(
            found=True,
            name=data["name"],
            department=data["department"],
            designation=data.get("designation", ""),
            message=message
        )
    return jsonify(found=False, message=message)


# ── Coordinator OTP Verification ──────────────────────────────────────

@authentication_bp.route("/coordinator/verify-otp", methods=["GET", "POST"])
def coordinator_verify_otp():
    """
    STEP 2: OTP Verification for coordinator login.
    Displays OTP input form and verifies OTP against challenge.
    """
    from flask import session
    from app.services.coordinator_otp_service import CoordinatorOTPService
    from app.extensions.mail import mail
    
    # Check if challenge token exists in session
    challenge_token = session.get('coordinator_challenge_token')
    if not challenge_token:
        flash("Verification session expired. Please login again.", "warning")
        return redirect(url_for('authentication.login') + '?tab=coordinator')
    
    error = None
    success_msg = None
    
    if request.method == "POST":
        action = request.form.get("action", "verify")
        
        if action == "verify":
            # Verify OTP
            otp = request.form.get("otp", "").strip()
            
            if not otp:
                error = "Please enter the OTP."
            elif len(otp) != 6 or not otp.isdigit():
                error = "OTP must be 6 digits."
            else:
                otp_service = CoordinatorOTPService(mail=mail)
                success, message, challenge = otp_service.verify_otp(challenge_token, otp)
                
                if success:
                    # OTP verified successfully - NOW create authenticated session
                    from app.models.user import User
                    from flask_login import login_user
                    
                    # Clear challenge from session
                    session.pop('coordinator_challenge_token', None)
                    session.pop('coordinator_challenge_created', None)
                    
                    # Find coordinator user
                    coord_user = User.query.filter_by(role="super_admin").first()
                    if not coord_user:
                        # Fallback
                        employee = _emp_repo.get_by_code("E-2606026")
                        if employee:
                            coord_user = User.query.filter_by(id=employee.user_id).first()
                    
                    if coord_user:
                        login_user(coord_user, remember=False)
                        coord_user.record_successful_login(request.remote_addr)
                        flash("Login successful!", "success")
                        return redirect(url_for("coordinator.dashboard"))
                    else:
                        error = "Coordinator account not found. Please contact administrator."
                else:
                    error = message
        
        elif action == "resend":
            # Resend OTP
            otp_service = CoordinatorOTPService(mail=mail)
            cooldown = int(current_app.config.get('OTP_RESEND_COOLDOWN_SECONDS', 60))
            success, message, new_otp = otp_service.resend_otp(challenge_token, cooldown)
            
            if success and new_otp:
                # Send new OTP to recipients
                recipients_str = current_app.config.get('COORDINATOR_OTP_RECIPIENTS', '')
                recipients = [email.strip() for email in recipients_str.split(',') if email.strip()]
                
                email_success, email_message = otp_service.send_otp_email(new_otp, recipients)
                
                if email_success:
                    success_msg = "New OTP sent successfully. Please check your email."
                else:
                    error = "Failed to send new OTP. Please try again."
            else:
                error = message
    
    return render_template(
        "authentication/coordinator_otp_verify.html",
        title="Coordinator OTP Verification",
        error=error,
        success_msg=success_msg,
        challenge_token=challenge_token
    )


@authentication_bp.route("/coordinator/cancel-otp", methods=["POST"])
def coordinator_cancel_otp():
    """Cancel OTP verification and return to login."""
    from flask import session
    from app.services.coordinator_otp_service import CoordinatorOTPService
    from app.extensions.mail import mail
    
    challenge_token = session.get('coordinator_challenge_token')
    if challenge_token:
        # Invalidate challenge
        otp_service = CoordinatorOTPService(mail=mail)
        otp_service.invalidate_challenge(challenge_token)
        
        # Clear session
        session.pop('coordinator_challenge_token', None)
        session.pop('coordinator_challenge_created', None)
    
    return redirect(url_for('authentication.login') + '?tab=coordinator')


# ── Logout ────────────────────────────────────────────────────────────

@authentication_bp.route("/logout")
@login_required
def logout():
    _svc.logout_current_user()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("authentication.login"))


# ── Refresh Session (Force role update) ────────────────────────────────

@authentication_bp.route("/refresh-session")
@login_required
def refresh_session():
    """
    Force refresh the current user session from database.
    This ensures role changes take effect immediately without logout.
    """
    from flask_login import fresh_login_required, request as flask_request
    from flask import session
    
    # Refresh the user from database
    from app.models.user import User  # noqa: PLC0415
    user = User.query.get(current_user.id)
    
    if user:
        # Clear the session and re-login with fresh user
        from flask_login import login_user, logout_user
        logout_user()
        login_user(user, remember=False)
        
        # Redirect to appropriate dashboard based on new role
        return redirect(_svc.get_dashboard_url(user))
    
    return redirect(url_for("authentication.login"))


# ── Forgot Password ───────────────────────────────────────────────────

@authentication_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    
    # Redirect to login page with forgot tab
    return redirect(url_for("authentication.login", tab="forgot"))


# ── Reset Password ────────────────────────────────────────────────────

@authentication_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form  = ResetPasswordForm()
    error = None

    if request.method == "POST":
        try:
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            
            # Manual validation
            if not password:
                error = "Password is required."
            elif not confirm_password:
                error = "Please confirm your password."
            elif password != confirm_password:
                error = "Passwords do not match."
            elif len(password) < 8:
                error = "Password must be at least 8 characters."
            else:
                # Try to reset password
                ok, msg = _svc.reset_password(token, password)
                if ok:
                    flash(msg, "success")
                    return redirect(url_for("authentication.login"))
                else:
                    error = msg
        except Exception as e:
            error = f"An error occurred: {str(e)}"
    
    return render_template(
        "authentication/reset_password.html",
        title="Reset Password",
        form=form,
        token=token,
        error=error,
    )


# ═════════════════════════════════════════════════════════════════════════
# COORDINATOR ATTENDANCE PORTAL
# ═════════════════════════════════════════════════════════════════════════
# NOTE: Coordinator API endpoints are NOW registered directly with the Flask
# app (not through this blueprint) to bypass Flask-Login authentication.
# See: app/blueprints/coordinator/routes.py
# 
# Routes available:
#   - /coordinator/portal (GET) - serves the portal HTML
#   - /coordinator/api/search-employee (POST) - searches employee
#   - /coordinator/api/submit-attendance (POST) - submits attendance
#   - /coordinator/api/get-gps (POST) - returns GPS coordinates
