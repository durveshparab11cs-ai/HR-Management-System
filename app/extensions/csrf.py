"""
app/extensions/csrf.py
=======================
Flask-WTF CSRF Protection extension instance.

Provides global CSRF protection for all state-changing requests (POST, PUT,
PATCH, DELETE). API blueprints that use token-based authentication can
exempt themselves using @csrf.exempt on their blueprint.

The CSRF token is automatically injected into all WTForms forms via the
{{ form.hidden_tag() }} call in templates, or manually via
{{ csrf_token() }} for AJAX requests.
"""

from flask_wtf.csrf import CSRFProtect

# Single CSRFProtect instance.
csrf: CSRFProtect = CSRFProtect()
