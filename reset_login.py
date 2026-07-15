"""Clear login history and unlock all accounts. python reset_login.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['FLASK_ENV'] = 'development'
from dotenv import load_dotenv; load_dotenv()
from app import create_app
app = create_app('development')
with app.app_context():
    from app.extensions.database import db
    from app.models.login_history import LoginHistory
    from app.models.user import User
    deleted = db.session.query(LoginHistory).delete()
    # Unlock all users and reset failed attempts
    users = User.query.all()
    for u in users:
        u.failed_login_attempts = 0
        u.locked_until = None
        db.session.add(u)
    db.session.commit()
    print(f"Deleted {deleted} login history records. All accounts unlocked.")
