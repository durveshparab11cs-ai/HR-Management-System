"""
app/extensions/mail.py
=======================
Flask-Mail extension instance.

Provides email sending capabilities throughout the application.
Configuration is read from Flask app config (MAIL_SERVER, MAIL_PORT, etc.)
which in turn reads from environment variables.

Usage:
    from app.extensions import mail
    with mail.connect() as conn:
        conn.send(message)
"""

from flask_mail import Mail

# Single Mail instance for the entire application.
mail: Mail = Mail()
