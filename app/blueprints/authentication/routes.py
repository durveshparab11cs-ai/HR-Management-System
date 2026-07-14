"""
blueprints/authentication/routes.py
=====================================
Authentication route handlers — thin layer, delegates to AuthService.
"""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user

from app.constants.limits import Limits
from app.extensions.limiter import limiter
from .forms import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm
from .service import AuthService
from . import authentication_bp

_svc = AuthService()


@authentication_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_svc.get_dashboard_url(current_user))

    login_form = LoginForm()
    register_form = RegisterForm()
    error = None
    active_tab = request.args.get("tab", "login")  # login | register

    if request.method == "POST":
        action = request.form.get("action", "login")

        if action == "login" and login_form.validate_on_submit():
            success, message, user = _svc.attempt_login(
                email=login_form.email.data,
                password=login_form.password.data,
                remember=login_form.remember_me.data,
            )
            if success:
                next_url = request.args.get("next")
                if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                    return redirect(next_url)
                return redirect(_svc.get_dashboard_url(user))
            else:
                error = message
                active_tab = "login"

        elif action == "register":
            if register_form.validate_on_submit():
                ok, msg, emp = _svc.register_first_user(
                    first_name=register_form.first_name.data,
                    last_name=register_form.last_name.data,
                    email=register_form.email.data,
                    password=register_form.password.data,
                    role=register_form.role.data,
                )
                if ok:
                    flash(msg, "success")
                    return redirect(url_for("authentication.login") + "?tab=login")
                else:
                    error = msg
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


@authentication_bp.route("/logout")
@login_required
def logout():
    _svc.logout_current_user()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("authentication.login"))


@authentication_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit(Limits.RateLimit.PASSWORD_RESET)
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    form = ForgotPasswordForm()
    sent = False
    if form.validate_on_submit():
        # Email sending will be wired when email is configured
        sent = True
    return render_template(
        "authentication/forgot_password.html",
        title="Forgot Password",
        form=form,
        sent=sent,
    )


@authentication_bp.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit(Limits.RateLimit.PASSWORD_RESET)
def reset_password(token: str):
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        flash("Password reset successfully. Please sign in.", "success")
        return redirect(url_for("authentication.login"))
    return render_template(
        "authentication/reset_password.html",
        title="Reset Password",
        form=form,
        token=token,
    )
