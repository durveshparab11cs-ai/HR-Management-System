"""
blueprints/authentication/repository.py
==========================================
Authentication repository — database access for auth operations.
"""

from datetime import datetime, timezone
from typing import Optional

from app.extensions.database import db
from app.models.user import User
from app.models.login_history import LoginHistory


class AuthRepository:

    def get_by_email(self, email: str) -> Optional[User]:
        return User.query.filter_by(email=email.lower().strip(), is_deleted=False).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return User.query.filter_by(id=user_id, is_deleted=False).first()

    def record_login(
        self,
        user_id: Optional[int],
        email: str,
        success: bool,
        ip: Optional[str],
        user_agent: Optional[str],
        failure_reason: Optional[str] = None,
    ) -> LoginHistory:
        entry = LoginHistory(
            user_id=user_id,
            email_attempted=email.lower().strip(),
            success=success,
            ip_address=ip,
            user_agent=user_agent[:255] if user_agent else None,
            failure_reason=failure_reason,
            timestamp=datetime.now(timezone.utc),
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    def get_login_history(self, user_id: int, limit: int = 20):
        return (
            LoginHistory.query
            .filter_by(user_id=user_id)
            .order_by(LoginHistory.timestamp.desc())
            .limit(limit)
            .all()
        )

    def update_user(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

    def create_user(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user
