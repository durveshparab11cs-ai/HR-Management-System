"""
app/services/coordinator_otp_service.py
========================================
Service for coordinator OTP generation, validation, and email delivery.

Handles secure OTP generation, bcrypt hashing, email sending to multiple
recipients, and OTP verification with rate limiting.
"""

import secrets
import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional

from flask import current_app
from flask_mail import Message, Mail
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions.database import db
from app.models.coordinator_otp import CoordinatorOTP

logger = logging.getLogger(__name__)


class CoordinatorOTPService:
    """Service for managing coordinator OTP challenges and email delivery."""

    def __init__(self, mail: Optional[Mail] = None):
        """Initialize OTP service with optional Mail instance."""
        self.mail = mail

    def generate_otp(self) -> str:
        """
        Generate a secure random 6-digit OTP.
        
        Returns:
            6-digit OTP as string
        """
        # Generate cryptographically secure 6-digit OTP
        otp = str(secrets.randbelow(1000000)).zfill(6)
        return otp

    def generate_challenge_token(self) -> str:
        """
        Generate a unique challenge token for session identification.
        
        Returns:
            64-character hex token
        """
        return secrets.token_hex(32)

    def create_challenge(
        self,
        otp: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expiry_minutes: int = 5
    ) -> CoordinatorOTP:
        """
        Create a new OTP challenge with secure hash storage.
        
        Args:
            otp: The plaintext OTP (will be hashed)
            ip_address: Client IP address
            user_agent: Client user agent
            expiry_minutes: OTP expiration time in minutes
            
        Returns:
            CoordinatorOTP challenge instance
        """
        challenge = CoordinatorOTP(
            otp_hash=generate_password_hash(otp),
            challenge_token=self.generate_challenge_token(),
            expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(challenge)
        db.session.commit()
        
        logger.info(f"Created OTP challenge {challenge.challenge_token[:8]}... expires in {expiry_minutes} min")
        return challenge

    def send_otp_email(self, otp: str, recipients: list[str]) -> Tuple[bool, str]:
        """
        Send OTP to multiple recipients.
        
        Args:
            otp: The 6-digit OTP
            recipients: List of email addresses
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.mail:
            logger.error("Mail instance not configured")
            return False, "Email service not configured"
        
        if not recipients:
            logger.error("No recipients provided")
            return False, "No email recipients configured"
        
        try:
            # Create professional security email
            subject = "Smart HRMS — Coordinator Login Verification"
            
            body = f"""Smart HRMS — Coordinator Login Verification

Your OTP for Coordinator Portal login is:

{otp}

This OTP expires in 5 minutes and can be used only once.

IMPORTANT SECURITY NOTICE:
• Do not share this OTP with anyone except the authorized coordinator completing this login.
• If you did not expect this login attempt, please contact the HR/security administrator immediately.
• This OTP is for the Coordinator Portal (Attendance Kiosk) access only.

The coordinator must contact you to obtain this OTP.

---
Smart HRMS Security Team
This is an automated security notification. Do not reply to this email.
"""
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .otp-box {{ background: white; border: 2px solid #667eea; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0; }}
        .otp {{ font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 8px; }}
        .warning {{ background: #fff5f5; border-left: 4px solid #c53030; padding: 15px; margin: 20px 0; }}
        .footer {{ background: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">🛡️ Smart HRMS Security</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">Coordinator Login Verification</p>
        </div>
        <div class="content">
            <p>Your OTP for <strong>Coordinator Portal</strong> login is:</p>
            
            <div class="otp-box">
                <div class="otp">{otp}</div>
                <p style="margin: 10px 0 0 0; color: #666; font-size: 14px;">Expires in 5 minutes</p>
            </div>
            
            <p><strong>This OTP can be used only once.</strong></p>
            
            <div class="warning">
                <h4 style="margin: 0 0 10px 0; color: #c53030;">⚠️ IMPORTANT SECURITY NOTICE</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Do not share this OTP with anyone except the <strong>authorized coordinator</strong> completing this login.</li>
                    <li>If you did not expect this login attempt, please <strong>contact the HR/security administrator immediately</strong>.</li>
                    <li>This OTP is for the <strong>Coordinator Portal (Attendance Kiosk)</strong> access only.</li>
                </ul>
            </div>
            
            <p style="margin-top: 20px; color: #666;">The coordinator must contact you by phone to obtain this OTP.</p>
        </div>
        <div class="footer">
            <p style="margin: 0;">Smart HRMS Security Team</p>
            <p style="margin: 5px 0 0 0;">This is an automated security notification. Do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
            
            # Send to all recipients
            msg = Message(
                subject=subject,
                recipients=recipients,
                body=body,
                html=html_body
            )
            
            self.mail.send(msg)
            
            logger.info(f"OTP email sent successfully to {len(recipients)} recipients")
            return True, "OTP sent successfully"
            
        except Exception as e:
            logger.error(f"Failed to send OTP email: {e}", exc_info=True)
            return False, "Failed to send OTP email. Please try again."

    def verify_otp(self, challenge_token: str, otp: str) -> Tuple[bool, str, Optional[CoordinatorOTP]]:
        """
        Verify OTP against challenge.
        
        Args:
            challenge_token: The challenge token
            otp: The OTP to verify
            
        Returns:
            Tuple of (success: bool, message: str, challenge: Optional[CoordinatorOTP])
        """
        # Find challenge
        challenge = CoordinatorOTP.query.filter_by(challenge_token=challenge_token).first()
        
        if not challenge:
            logger.warning(f"Challenge not found: {challenge_token[:8]}...")
            return False, "Invalid or expired verification session. Please restart login.", None
        
        # Check if challenge is valid
        if not challenge.is_valid():
            if challenge.is_used:
                msg = "This OTP has already been used."
            elif challenge.is_invalidated:
                msg = "This verification session has been invalidated."
            elif challenge.is_expired():
                msg = "This OTP has expired. Please request a new OTP."
            elif challenge.attempt_count >= challenge.max_attempts:
                msg = "Too many failed attempts. Please restart login."
            else:
                msg = "Invalid verification session."
            
            logger.warning(f"Invalid challenge {challenge_token[:8]}...: {msg}")
            return False, msg, challenge
        
        # Verify OTP
        if check_password_hash(challenge.otp_hash, otp):
            # Success
            challenge.mark_used()
            db.session.commit()
            logger.info(f"OTP verified successfully for challenge {challenge_token[:8]}...")
            return True, "OTP verified successfully", challenge
        else:
            # Failed attempt
            challenge.increment_attempts()
            db.session.commit()
            
            remaining = challenge.max_attempts - challenge.attempt_count
            if remaining > 0:
                msg = f"Invalid OTP. {remaining} attempt(s) remaining."
            else:
                challenge.invalidate()
                db.session.commit()
                msg = "Invalid OTP. Maximum attempts reached. Please restart login."
            
            logger.warning(f"Invalid OTP for challenge {challenge_token[:8]}... (attempt {challenge.attempt_count})")
            return False, msg, challenge

    def resend_otp(self, challenge_token: str, cooldown_seconds: int = 60) -> Tuple[bool, str, Optional[str]]:
        """
        Resend OTP (generates new OTP and invalidates old one).
        
        Args:
            challenge_token: The challenge token
            cooldown_seconds: Minimum seconds between resends
            
        Returns:
            Tuple of (success: bool, message: str, new_otp: Optional[str])
        """
        # Find challenge
        challenge = CoordinatorOTP.query.filter_by(challenge_token=challenge_token).first()
        
        if not challenge:
            return False, "Invalid verification session.", None
        
        # Check if already used
        if challenge.is_used:
            return False, "This verification session has already been completed.", None
        
        # Check resend cooldown
        if not challenge.can_resend(cooldown_seconds):
            time_left = cooldown_seconds - (datetime.utcnow() - challenge.last_resend_at).total_seconds()
            return False, f"Please wait {int(time_left)} seconds before requesting another OTP.", None
        
        # Check resend limit
        if challenge.resend_count >= 3:
            challenge.invalidate()
            db.session.commit()
            return False, "Too many resend requests. Please restart login.", None
        
        # Generate new OTP
        new_otp = self.generate_otp()
        challenge.otp_hash = generate_password_hash(new_otp)
        challenge.expires_at = datetime.utcnow() + timedelta(minutes=5)
        challenge.mark_resent()
        challenge.attempt_count = 0  # Reset attempts
        db.session.commit()
        
        logger.info(f"OTP resent for challenge {challenge_token[:8]}... (resend #{challenge.resend_count})")
        return True, "New OTP generated and sent", new_otp

    def cleanup_expired_challenges(self, hours: int = 24) -> int:
        """
        Clean up expired challenges older than specified hours.
        
        Args:
            hours: Delete challenges older than this many hours
            
        Returns:
            Number of deleted challenges
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        count = CoordinatorOTP.query.filter(CoordinatorOTP.created_at < cutoff).delete()
        db.session.commit()
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired OTP challenges")
        
        return count

    def invalidate_challenge(self, challenge_token: str) -> bool:
        """
        Manually invalidate a challenge.
        
        Args:
            challenge_token: The challenge token
            
        Returns:
            True if invalidated, False if not found
        """
        challenge = CoordinatorOTP.query.filter_by(challenge_token=challenge_token).first()
        if challenge:
            challenge.invalidate()
            db.session.commit()
            logger.info(f"Challenge {challenge_token[:8]}... manually invalidated")
            return True
        return False
