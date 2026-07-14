"""
app/utils/email_utils.py
=========================
Email composition and sending helpers.

Wraps Flask-Mail to provide a clean API for sending transactional emails.
All email templates are rendered from the templates/emails/ directory.

Design principles:
    - Never send email synchronously inside a request handler.
    - Use a background thread or task queue for sending.
    - Always render both HTML and plain-text versions.
    - Log all send attempts (success and failure).
"""

import logging
import threading
from typing import Optional

from flask import current_app, render_template
from flask_mail import Message

from app.extensions.mail import mail

logger = logging.getLogger(__name__)


def send_email(
    subject: str,
    recipients: list[str],
    template: str,
    context: Optional[dict] = None,
    sender: Optional[str] = None,
    cc: Optional[list[str]] = None,
    bcc: Optional[list[str]] = None,
    attachments: Optional[list[tuple]] = None,
    async_send: bool = True,
) -> bool:
    """
    Compose and send an email using a Jinja2 template pair.

    Looks for:
        templates/emails/<template>.html  — HTML version
        templates/emails/<template>.txt   — Plain-text version

    Args:
        subject: Email subject line.
        recipients: List of recipient email addresses.
        template: Template name without extension (e.g., 'welcome').
        context: Dictionary of variables passed to the template.
        sender: Override sender address (defaults to MAIL_DEFAULT_SENDER).
        cc: Carbon-copy recipient list.
        bcc: Blind carbon-copy recipient list.
        attachments: List of (filename, content_type, data) tuples.
        async_send: If True, send in a background thread.

    Returns:
        True if email was queued/sent successfully, False on error.
    """
    context = context or {}
    app = current_app._get_current_object()  # noqa: SLF001 — needed for thread safety

    try:
        html_body = render_template(f"emails/{template}.html", **context)
        try:
            text_body = render_template(f"emails/{template}.txt", **context)
        except Exception:  # noqa: BLE001
            text_body = None  # Plain-text version is optional

        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html_body,
            body=text_body,
            sender=sender or app.config.get("MAIL_DEFAULT_SENDER"),
            cc=cc,
            bcc=bcc,
        )

        if attachments:
            for filename, content_type, data in attachments:
                msg.attach(filename, content_type, data)

        if async_send:
            thread = threading.Thread(
                target=_send_async,
                args=(app, msg),
                daemon=True,
            )
            thread.start()
        else:
            with app.app_context():
                mail.send(msg)

        logger.info("Email queued | subject=%r | to=%s", subject, recipients)
        return True

    except Exception as exc:  # noqa: BLE001
        logger.error("Email send failed | subject=%r | to=%s | error=%s", subject, recipients, exc)
        return False


def send_password_reset_email(user_email: str, user_name: str, reset_url: str) -> bool:
    """
    Send a password reset email to the user.

    Args:
        user_email: Recipient's email address.
        user_name: Recipient's first name for personalization.
        reset_url: Full URL containing the password reset token.

    Returns:
        True if the email was queued successfully.
    """
    return send_email(
        subject="Reset Your Smart HRMS Password",
        recipients=[user_email],
        template="password_reset",
        context={"user_name": user_name, "reset_url": reset_url},
    )


def send_verification_email(user_email: str, user_name: str, verify_url: str) -> bool:
    """
    Send an email verification link to a newly registered user.

    Args:
        user_email: Recipient's email address.
        user_name: Recipient's first name.
        verify_url: Full verification URL.

    Returns:
        True if the email was queued successfully.
    """
    return send_email(
        subject="Verify Your Smart HRMS Email Address",
        recipients=[user_email],
        template="email_verification",
        context={"user_name": user_name, "verify_url": verify_url},
    )


def send_welcome_email(user_email: str, user_name: str, login_url: str) -> bool:
    """
    Send a welcome email to a newly created employee account.

    Args:
        user_email: Recipient's email address.
        user_name: Recipient's first name.
        login_url: Login page URL.

    Returns:
        True if the email was queued successfully.
    """
    return send_email(
        subject="Welcome to Smart HRMS",
        recipients=[user_email],
        template="welcome",
        context={"user_name": user_name, "login_url": login_url},
    )


def _send_async(app, msg: Message) -> None:
    """
    Internal helper to send email inside an app context in a thread.

    Args:
        app: The Flask application instance (not proxy).
        msg: Flask-Mail Message object.
    """
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as exc:  # noqa: BLE001
            logger.error("Async email send error: %s", exc)
