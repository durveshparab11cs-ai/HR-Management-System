"""
app/extensions/session.py
==========================
Flask-Session extension instance for server-side session storage.

Stores session data on the server (filesystem or Redis) instead of
the client-side cookie, improving security for sensitive session data.

Session backends:
    Development  — filesystem (./instance/sessions/)
    Production   — Redis (shared across workers, persistent)

Note: The extension is named server_session to avoid shadowing
Flask's built-in flask.session proxy object.
"""

from flask_session import Session

# Single Session instance.
# Named server_session to avoid shadowing Flask's session proxy.
server_session: Session = Session()
