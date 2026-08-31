from app import create_app
app = create_app('production')
print(f'Database: {app.config.get("SQLALCHEMY_DATABASE_URI")}')
