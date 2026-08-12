import os
import sys
from pathlib import Path
os.environ['FLASK_ENV'] = 'production'
sys.path.insert(0, str(Path.cwd()))
from dotenv import load_dotenv
load_dotenv()
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    os.environ['DATABASE_URL'] = db_url.replace('postgres://', 'postgresql://', 1)

from app import create_app
from app.models.hospital import Hospital
from app.extensions.database import db

app = create_app('production')
with app.app_context():
    ho = Hospital.query.filter_by(hospital_name='Head office').first()
    if ho:
        ho.allowed_radius_metres = 150
        db.session.commit()
        print(f'Updated Head office radius to {ho.allowed_radius_metres}m')
    else:
        print('Head office not found')
