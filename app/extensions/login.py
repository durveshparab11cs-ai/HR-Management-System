"""
app/extensions/login.py
========================
Flask-Login extension instance and configuration.

Handles user session management: loading users from the session,
protecting routes with @login_required, and managing remember-me tokens.

The user_loader callback is registered here and must return a User model
instance (or None) given a user ID stored in the session.
"""

from flask_login import LoginManager

login_manager: LoginManager = LoginManager()


def configure_login_manager(app) -> None:
    """
    Apply Flask-Login configuration to the app.

    Called from the application factory after init_app().
    Registers the user_loader callback by importing the User model
    inside the function to avoid circular imports.

    Args:
        app: The Flask application instance.
    """
    login_manager.login_view = app.config.get("LOGIN_VIEW", "authentication.login")
    login_manager.login_message = app.config.get(
        "LOGIN_MESSAGE", "Please log in to access this page."
    )
    login_manager.login_message_category = app.config.get(
        "LOGIN_MESSAGE_CATEGORY", "warning"
    )
    login_manager.session_protection = "strong"
    login_manager.refresh_view = "authentication.login"
    login_manager.needs_refresh_message = "Please re-authenticate to continue."
    login_manager.needs_refresh_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id: str):
        """
        Load a user from the database by their primary key.

        Flask-Login calls this on every request that has a user session.
        Returns None if the user no longer exists (e.g., deleted account).

        Args:
            user_id: String representation of the user's primary key.

        Returns:
            User instance or None.
        """
        # Import here to avoid circular import at module load time.
        from app.models.user import User  # noqa: PLC0415

        try:
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        """
        Custom handler for unauthorized access attempts.
        Redirects to the login page with a flash message.
        """
        from flask import flash, redirect, request, url_for  # noqa: PLC0415

        flash(login_manager.login_message, login_manager.login_message_category)
        return redirect(url_for(login_manager.login_view, next=request.url))
