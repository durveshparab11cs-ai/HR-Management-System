"""
blueprints/authentication/routes.py
=====================================
Authentication routes — Employee Code-based login and registration.
"""

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.constants.limits import Limits
from app.extensions.limiter import limiter
from .forms import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm
from .service import AuthService
from . import authentication_bp

_svc = AuthService()


# ── Login / Register ──────────────────────────────────────────────────

@authentication_bp.route("/login", methods=["GET", "POST"])
@limiter.limit(Limits.RateLimit.LOGIN)
def login():
    if current_user.is_authenticated:
        return redirect(_svc.get_dashboard_url(current_user))

    login_form    = LoginForm()
    register_form = RegisterForm()
    error         = None
    active_tab    = request.args.get("tab", "login")

    if request.method == "POST":
        action = request.form.get("action", "login")

        if action == "login":
            if login_form.validate_on_submit():
                success, message, user = _svc.attempt_login(
                    employee_code=login_form.employee_code.data,
                    password=login_form.password.data,
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
                active_tab = "login"

        elif action == "register":
            if register_form.validate_on_submit():
                ok, msg, user = _svc.register_by_code(
                    employee_code=register_form.employee_code.data,
                    password=register_form.password.data,
                )
                if ok:
                    flash(msg, "success")
                    return redirect(url_for("authentication.login") + "?tab=login")
                error      = msg
                active_tab = "register"
            else:
                active_tab = "register"

    return render_template(
        "authentication/login.html",
        title="Sign In",
        login_form=login_form,
        register_form=register_form,
        error=error,
        active_tab=active_tab,
    )


# ── AJAX: look up employee name from master ────────────────────────────

@authentication_bp.route("/lookup-employee")
def lookup_employee():
    """
    AJAX endpoint called by the registration form to fetch employee name.
    GET /auth/lookup-employee?code=E-2603028
    Returns JSON {found, name, department, message}
    """
    code = request.args.get("code", "").strip().upper()
    if not code:
        return jsonify(found=False, message="Enter an Employee Code.")

    found, message, data = _svc.lookup_employee(code)
    if found:
        return jsonify(found=True, name=data["name"],
                       department=data["department"], message=message)
    return jsonify(found=False, message=message)


# ── Logout ────────────────────────────────────────────────────────────

@authentication_bp.route("/logout")
@login_required
def logout():
    _svc.logout_current_user()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("authentication.login"))


# ── Forgot Password ───────────────────────────────────────────────────

@authentication_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit(Limits.RateLimit.PASSWORD_RESET)
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form    = ForgotPasswordForm()
    result  = None
    token   = None
    success = False

    if form.validate_on_submit():
        ok, payload = _svc.initiate_password_reset(form.employee_code.data)
        if ok:
            success = True
            token   = payload   # raw token — admin gives this to the employee
            result  = "Reset token generated. Please give this token to the employee."
        else:
            result = payload

    return render_template(
        "authentication/forgot_password.html",
        title="Forgot Password",
        form=form,
        result=result,
        success=success,
        token=token,
    )


# ── Reset Password ────────────────────────────────────────────────────

@authentication_bp.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit(Limits.RateLimit.PASSWORD_RESET)
def reset_password(token: str):
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form  = ResetPasswordForm()
    error = None

    if form.validate_on_submit():
        ok, msg = _svc.reset_password(token, form.password.data)
        if ok:
            flash(msg, "success")
            return redirect(url_for("authentication.login"))
        error = msg

    return render_template(
        "authentication/reset_password.html",
        title="Reset Password",
        form=form,
        token=token,
        error=error,
    )
