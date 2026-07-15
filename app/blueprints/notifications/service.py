"""
blueprints/notifications/service.py
======================================
Notification service — create, fetch, mark-read, bulk-send.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.extensions.database import db
from app.models.notification import Notification

logger = logging.getLogger(__name__)


class NotificationService:

    def get_user_notifications(self, user_id: int, page: int = 1, per_page: int = 30):
        return (
            Notification.query
            .filter_by(user_id=user_id)
            .order_by(Notification.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    def get_unread_count(self, user_id: int) -> int:
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    def get_recent(self, user_id: int, limit: int = 8) -> list:
        return (
            Notification.query
            .filter_by(user_id=user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )

    def mark_read(self, notification_id: int, user_id: int) -> bool:
        n = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if not n:
            return False
        n.is_read = True
        n.read_at = datetime.utcnow()
        db.session.commit()
        return True

    def mark_all_read(self, user_id: int) -> int:
        count = (
            Notification.query
            .filter_by(user_id=user_id, is_read=False)
            .update({"is_read": True, "read_at": datetime.utcnow()})
        )
        db.session.commit()
        return count

    def create(
        self,
        user_id: int,
        title: str,
        message: str,
        category: str = "info",
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        triggered_by: Optional[int] = None,
    ) -> Notification:
        n = Notification(
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            action_url=action_url,
            action_label=action_label,
            triggered_by=triggered_by,
        )
        db.session.add(n)
        db.session.commit()
        logger.info("NOTIFICATION | user=%s | title=%r | category=%s", user_id, title, category)
        return n

    def send_to_all_active(
        self,
        title: str,
        message: str,
        category: str = "info",
        action_url: Optional[str] = None,
        triggered_by: Optional[int] = None,
    ) -> int:
        """Broadcast a notification to all active users."""
        from app.models.user import User
        from app.constants.enums import UserStatus
        users = User.query.filter_by(status=UserStatus.ACTIVE.value, is_deleted=False).all()
        for user in users:
            n = Notification(
                user_id=user.id,
                title=title,
                message=message,
                category=category,
                action_url=action_url,
                triggered_by=triggered_by,
            )
            db.session.add(n)
        db.session.commit()
        return len(users)
