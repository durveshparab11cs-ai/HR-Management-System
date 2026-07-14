"""
blueprints/settings/routes.py
================================
Settings routes.
"""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import settings_bp


@settings_bp.route("/")
@settings_bp.route("")
@login_required
def index():
    return redirect(url_for("settings.profile"))


@settings_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    from app.blueprints.employees.repository import EmployeeRepository
    emp_repo = EmployeeRepository()
    employee = emp_repo.get_by_user_id(current_user.id)
    return render_template("settings/profile.html", title="My Profile", employee=employee)


@settings_bp.route("/security", methods=["GET", "POST"])
@login_required
def security():
    return render_template("settings/security.html", title="Security Settings")


@settings_bp.route("/notifications", methods=["GET", "POST"])
@login_required
def notification_preferences():
    return render_template("settings/notification_preferences.html", title="Notification Preferences")


@settings_bp.route("/leave-policy", methods=["GET", "POST"])
@login_required
def leave_policy():
    return redirect(url_for("admin.office_settings"))
