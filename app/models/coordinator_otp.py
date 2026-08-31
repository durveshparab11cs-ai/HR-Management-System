"""
app/models/coordinator_otp.py
==============================
Coordinator OTP authentication challenges for two-factor authentication.

Stores OTP challenges for coordinator portal login with secure hashing,
expiration, and usage tracking.
"""

from datetime import datetime, timedelta
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions.database import db


class CoordinatorOTP(db.Model):
    """OTP challenges for coordinator two-factor authentication."""

    __tablename__ = "coordinator_otp_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # OTP stored as secure hash (bcrypt)
    otp_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt hash of the 6-digit OTP"
    )

    # Challenge tracking
    challenge_token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique token to identify this challenge session"
    )

    # Security metadata
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of failed OTP verification attempts"
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        doc="Maximum allowed verification attempts"
    )

    # Status tracking
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="True if OTP has been successfully verified"
    )

    is_invalidated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="True if challenge has been manually invalidated"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="When the challenge was created"
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        doc="When the OTP expires"
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        doc="When the OTP was successfully verified"
    )

    invalidated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        doc="When the challenge was invalidated"
    )

    # Rate limiting for resend
    last_resend_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        doc="Last time OTP was resent"
    )

    resend_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of times OTP has been resent"
    )

    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        doc="IP address that initiated the challenge"
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="User agent string"
    )

    def is_expired(self) -> bool:
        """Check if the OTP has expired."""
        return datetime.utcnow() >= self.expires_at

    def is_valid(self) -> bool:
        """Check if the challenge is still valid for verification."""
        return (
            not self.is_used
            and not self.is_invalidated
            and not self.is_expired()
            and self.attempt_count < self.max_attempts
        )

    def can_resend(self, cooldown_seconds: int = 60) -> bool:
        """Check if OTP can be resent (respects cooldown)."""
        if not self.last_resend_at:
            return True
        time_since_last = datetime.utcnow() - self.last_resend_at
        return time_since_last.total_seconds() >= cooldown_seconds

    def increment_attempts(self) -> None:
        """Increment failed attempt counter."""
        self.attempt_count += 1

    def mark_used(self) -> None:
        """Mark OTP as successfully verified."""
        self.is_used = True
        self.used_at = datetime.utcnow()

    def invalidate(self) -> None:
        """Invalidate the challenge."""
        self.is_invalidated = True
        self.invalidated_at = datetime.utcnow()

    def mark_resent(self) -> None:
        """Update resend metadata."""
        self.last_resend_at = datetime.utcnow()
        self.resend_count += 1

    def __repr__(self) -> str:
        return f"<CoordinatorOTP id={self.id} token={self.challenge_token[:8]}... valid={self.is_valid()}>"
