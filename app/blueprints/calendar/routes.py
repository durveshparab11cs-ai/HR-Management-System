"""
blueprints/calendar/routes.py
===============================
Calendar blueprint routes for holiday display and management.
"""

from datetime import datetime
from flask import flash, jsonify, redirect, render_template, request, url_for, send_file
from flask_login import current_user, login_required

from app.core.security import admin_required
from app.services.holiday_service import HolidayService
from .forms import HolidayImportForm
from . import calendar_bp

_svc = HolidayService()


@calendar_bp.route("/")
@login_required
def index():
    """Display the holiday calendar for current month/year."""
    year = request.args.get("year", datetime.now().year, type=int)
    month = request.args.get("month", datetime.now().month, type=int)

    # Validate month/year
    if month < 1:
        month = 1
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    # Get holidays for the year
    holidays = _svc.get_holidays_by_year(year)

    # Get available years for the selector
    years = _svc.get_available_years()

    return render_template(
        "calendar/index.html",
        title="Holiday Calendar",
        year=year,
        month=month,
        holidays=holidays,
        available_years=years,
    )


@calendar_bp.route("/api/holidays")
@login_required
def api_holidays():
    """API endpoint to get holidays for a specific year (JSON)."""
    year = request.args.get("year", datetime.now().year, type=int)

    holidays = _svc.get_holidays_by_year(year)

    return jsonify({
        "success": True,
        "year": year,
        "holidays": [h.to_dict() for h in holidays],
    })


@calendar_bp.route("/holiday/<int:holiday_id>")
@login_required
def holiday_detail(holiday_id: int):
    """Display details for a specific holiday."""
    holiday = _svc.get_holiday_by_id(holiday_id)

    if not holiday:
        flash("Holiday not found.", "danger")
        return redirect(url_for("calendar.index"))

    return render_template(
        "calendar/holiday_detail.html",
        title="Holiday Details",
        holiday=holiday,
    )


@calendar_bp.route("/import", methods=["GET", "POST"])
@login_required
@admin_required
def import_holidays():
    """Import holidays from Excel file."""
    form = HolidayImportForm()

    if form.validate_on_submit():
        file = form.file.data
        result = _svc.import_from_excel(file)

        if result["success"]:
            flash(result["message"], "success")
            return redirect(url_for("calendar.index"))
        else:
            flash(result["message"], "danger")

    return render_template(
        "calendar/import.html",
        title="Import Holidays",
        form=form,
    )


@calendar_bp.route("/api/holiday/<int:holiday_id>")
@login_required
def api_holiday_detail(holiday_id: int):
    """API endpoint to get holiday details (JSON)."""
    holiday = _svc.get_holiday_by_id(holiday_id)

    if not holiday:
        return jsonify({"success": False, "error": "Holiday not found."}), 404

    return jsonify({
        "success": True,
        "holiday": holiday.to_dict(),
    })


@calendar_bp.route("/api/upload-holidays", methods=["POST"])
@login_required
@admin_required
def upload_holidays_api():
    """API endpoint to upload and import holidays from Excel."""
    try:
        file = request.files.get("file")
        if not file or file.filename == "":
            return jsonify({"success": False, "message": "No file selected"}), 400

        result = _svc.import_from_excel(file)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Holiday upload error: {e}")
        return jsonify({"success": False, "message": f"Upload error: {str(e)[:100]}"}), 500


@calendar_bp.route("/download-template")
@login_required
def download_template():
    """Download a template Excel file for holiday imports."""
    try:
        excel_file = _svc.generate_template_excel()
        return send_file(
            excel_file,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="holiday_template.xlsx",
        )
    except Exception as e:
        flash(f"Error generating template: {str(e)}", "danger")
        return redirect(url_for("calendar.index"))
