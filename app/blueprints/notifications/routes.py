"""blueprints/notifications/routes.py"""

from flask import jsonify, render_template, request
from flask_login import current_user, login_required

from .service import NotificationService
from . import notifications_bp

_svc = NotificationService()


@notifications_bp.route("/")
@notifications_bp.route("")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    pagination = _svc.get_user_notifications(current_user.id, page=page)
    unread = _svc.get_unread_count(current_user.id)
    return render_template(
        "notifications/index.html",
        title="Notifications",
        pagination=pagination,
        unread=unread,
    )


@notifications_bp.route("/count")
@login_required
def count():
    return jsonify({"unread": _svc.get_unread_count(current_user.id)})


@notifications_bp.route("/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id: int):
    ok = _svc.mark_read(notification_id, current_user.id)
    return jsonify({"success": ok})


@notifications_bp.route("/mark-all-read", methods=["POST"])
@login_required
def mark_all_read():
    count = _svc.mark_all_read(current_user.id)
    return jsonify({"success": True, "marked": count})
