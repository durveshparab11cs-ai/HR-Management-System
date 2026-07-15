"""
db_init.py
===========
Create all database tables from SQLAlchemy models.
Run from smart_hrms/ folder: python db_init.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("FLASK_ENV", "development")

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions.database import db

app = create_app("development")

with app.app_context():
    db.create_all()
    print("All tables created successfully.")

    # List tables created
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tables in database ({len(tables)}):")
    for t in sorted(tables):
        print(f"  - {t}")
