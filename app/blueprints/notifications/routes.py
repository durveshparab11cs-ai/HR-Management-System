"""blueprints/notifications/routes.py"""

from datetime import datetime
from flask import jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.notification import Notification
from app.extensions.database import db
from .service import NotificationService
from . import notifications_bp

_svc = NotificationService()


def _resolve_notification_target(n: Notification) -> str:
    """Determine the redirection URL for a notification."""
    if n and n.action_url:
        return n.action_url
    cat = getattr(n, "category", "") or ""
    title = (getattr(n, "title", "") or "").lower()
    if cat == "leave":
        if "request" in title:
            return "/leave/my-approvals"
        return "/leave"
    if cat == "attendance":
        return "/attendance/history"
    if cat == "payroll":
        return "/payroll"
    return "/dashboard"


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


@notifications_bp.route("/recent")
@login_required
def recent():
    """Return unread notifications for the navbar notification drawer."""
    limit = request.args.get("limit", 10, type=int)
    items = (
        Notification.query
        .filter_by(user_id=current_user.id, is_read=False)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    result = []
    for n in items:
        result.append({
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "category": n.category,
            "icon": n.icon,
            "color": n.color,
            "action_url": _resolve_notification_target(n),
            "created_at": n.created_at.strftime("%d %b, %I:%M %p") if n.created_at else "",
            "is_read": n.is_read,
        })
    return jsonify({
        "success": True,
        "notifications": result,
        "unread_count": len(result)
    })


@notifications_bp.route("/<int:notification_id>/click", methods=["GET", "POST"])
@login_required
def click_notification(notification_id: int):
    """Mark notification as read and redirect directly to destination page."""
    n = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    target_url = "/dashboard"
    if n:
        n.is_read = True
        n.read_at = datetime.utcnow()
        db.session.commit()
        target_url = _resolve_notification_target(n)

    if request.method == "POST":
        return jsonify({"success": True, "redirect_url": target_url})
    return redirect(target_url)


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
