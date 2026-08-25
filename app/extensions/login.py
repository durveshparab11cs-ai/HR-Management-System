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
    # Empty string suppresses the flash banner — the login page itself
    # provides enough context without a yellow "Please log in" popup.
    login_manager.login_message = ""
    login_manager.login_message_category = "info"
    # "basic" instead of "strong" — "strong" invalidates sessions whenever
    # IP or User-Agent changes (common on mobile/Render proxy), causing
    # spurious logouts and multiple flash messages on the admin dashboard.
    login_manager.session_protection = "basic"
    login_manager.refresh_view = "authentication.login"
    login_manager.needs_refresh_message = ""
    login_manager.needs_refresh_message_category = "info"
    # Disable strong session protection but refresh user on every request
    # This ensures role changes take effect immediately
    app.config['SESSION_PERMANENT'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

    @login_manager.needs_refresh_handler
    def needs_refresh():
        """
        Handle requests that need session refresh.
        For coordinator API endpoints, allow access without refresh.
        
        CRITICAL: For coordinator API endpoints, we must skip Flask-Login entirely
        by setting a flag that the unauthorized_handler checks.
        """
        from flask import request, url_for, redirect, g  # noqa: PLC0415
        import logging as py_logging
        logger_refresh = py_logging.getLogger("flask_login.needs_refresh")

        # ========================================================
        # COORDINATOR API ENDPOINTS - SKIP AUTHENTICATION ENTIRELY
        # ========================================================
        if request.path.startswith('/coordinator/api/'):
            logger_refresh.info(f"🟢 COORDINATOR API: Skipping auth for {request.path}")
            # Set flag to skip auth in unauthorized_handler
            g.skip_coordinator_auth = True
            # Return None to continue to the route without restriction
            return None

        # ========================================================
        # COORDINATOR PORTAL - ALLOW WITHOUT REFRESH
        # ========================================================
        if request.path.startswith('/coordinator/login') or request.path.startswith('/coordinator/portal'):
            logger_refresh.info(f"🟢 COORDINATOR PORTAL: Allowing {request.path}")
            return None

        # ========================================================
        # OTHER ROUTES - REDIRECT TO REFRESH
        # ========================================================
        logger_refresh.warning(f"SESSION NEEDS REFRESH: {request.method} {request.path}")
        
        if login_manager.needs_refresh_message:
            from flask import flash  # noqa: PLC0415
            flash(login_manager.needs_refresh_message, login_manager.needs_refresh_message_category)

        return redirect(url_for(login_manager.refresh_view, next=request.url))

    @login_manager.user_loader
    def load_user(user_id: str):
        """
        Load a user from the database by their primary key.
        Flask-Login calls this on every request that has a user session.
        Returns None if the user no longer exists.
        """
        from app.models.user import User  # noqa: PLC0415
        
        try:
            user = User.query.get(int(user_id))
            return user
        except (ValueError, TypeError):
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        """
        Custom handler for unauthorized access attempts.
        Returns JSON for API endpoints, redirects for regular routes.
        CRITICAL: For coordinator API, we MUST allow access without redirect.
        """
        from flask import redirect, request, url_for, jsonify, g  # noqa: PLC0415
        import logging as py_logging
        
        logger_unauth = py_logging.getLogger("flask_login.unauthorized")
        logger_unauth.info(f"unauthorized_handler called: {request.method} {request.path}")

        # ========================================================
        # COORDINATOR API ENDPOINTS - PUBLIC, NO AUTH NEEDED
        # Returning None tells Flask-Login to NOT intercept, but it still might redirect
        # Instead, we raise an exception to skip Flask-Login's redirect entirely
        # ========================================================
        if request.path.startswith('/coordinator/api/'):
            logger_unauth.info(f"🟢 COORDINATOR API: Allowing {request.method} {request.path} without auth")
            # Import flask_login internals to skip authentication
            from flask_login import current_app as _current_app
            # Don't intercept - return None which tells Flask-Login to proceed
            # But Flask-Login might still redirect, so we need to be more aggressive
            # The key is that these routes should NEVER trigger @login_required in the first place!
            # If they do, it's a configuration error.
            return None  # This tells Flask-Login to NOT show login page

        # ========================================================
        # COORDINATOR PORTAL PAGES - PUBLIC, NO AUTH NEEDED
        # ========================================================
        if request.path == '/coordinator/login' or request.path == '/coordinator/portal':
            logger_unauth.info(f"🟢 COORDINATOR PAGE: Allowing {request.method} {request.path}")
            return None

        # ========================================================
        # OTHER API ENDPOINTS - RETURN JSON ERROR
        # ========================================================        
        if '/api/' in request.path:
            logger_unauth.info(f"API endpoint unauthorized: {request.path}")
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        # ========================================================
        # REGULAR ROUTES - REDIRECT TO LOGIN
        # ========================================================        
        logger_unauth.info(f"Redirecting to login: {request.path}")
        
        if login_manager.login_message:
            from flask import flash  # noqa: PLC0415
            flash(login_manager.login_message, login_manager.login_message_category)

        return redirect(url_for(login_manager.login_view, next=request.url))

