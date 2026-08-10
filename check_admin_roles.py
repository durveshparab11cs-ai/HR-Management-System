from app import create_app
from app.extensions.database import db
from app.models.user import User

app = create_app()
with app.app_context():
    # Check current logged-in user or test admin users
    users = User.query.filter(User.username.in_(['e2606026', 'e_2512012', 'e_2603025'])).all()
    for u in users:
        print(f"User: {u.username}, Role: {u.role}, Role Type: {type(u.role).__name__}")
    
    # Check if there are any super_admin or admin users
    admins = User.query.filter(User.role.in_(['super_admin', 'admin'])).all()
    print(f"\nTotal admin/super_admin users: {len(admins)}")
    for admin in admins[:5]:
        print(f"  - {admin.username}: {admin.role}")
    
    # List all unique roles
    all_roles = db.session.query(User.role).distinct().all()
    print(f"\nAll unique roles in database:")
    for role in all_roles:
        print(f"  - {role[0]}")
