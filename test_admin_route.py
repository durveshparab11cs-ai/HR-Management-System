from app import create_app
from app.extensions.database import db
from flask_login import login_user
from app.models.user import User

app = create_app()

with app.app_context():
    with app.test_client() as client:
        # Get a super_admin user
        user = User.query.filter_by(username='e2512012').first()
        
        if not user:
            print("User not found!")
            exit(1)
        
        print(f"User: {user.username}, Role: {user.role}")
        
        # Try to login
        response = client.post('/auth/login', data={
            'username': user.username,
            'password': 'Test@123'  # Try default password
        })
        
        print(f"Login response status: {response.status_code}")
        
        # Try to access admin dashboard
        response = client.get('/admin/')
        print(f"Admin dashboard status: {response.status_code}")
        
        if response.status_code == 404:
            print("ERROR: 404 returned")
            print(f"Response: {response.data[:200]}")
        elif response.status_code == 403:
            print("ERROR: 403 Forbidden returned")
        elif response.status_code == 302:
            print("ERROR: 302 Redirect (need to login first)")
        else:
            print(f"SUCCESS: Admin dashboard loaded with status {response.status_code}")
