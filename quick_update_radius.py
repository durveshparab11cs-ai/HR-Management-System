import os
from dotenv import load_dotenv

load_dotenv()

try:
    import psycopg2
    db_url = os.environ.get('DATABASE_URL')
    
    # Parse PostgreSQL URL
    if db_url.startswith('postgresql://'):
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Update Head office radius
        cur.execute("UPDATE hospitals SET allowed_radius_metres = 150 WHERE hospital_name = %s", ('Head office',))
        conn.commit()
        
        # Check result
        cur.execute("SELECT hospital_name, allowed_radius_metres FROM hospitals WHERE hospital_name = %s", ('Head office',))
        result = cur.fetchone()
        
        if result:
            print(f'\n✅ SUCCESS:')
            print(f'   {result[0]}: {result[1]}m radius')
        else:
            print('\n❌ Head office not found')
        
        cur.close()
        conn.close()
    else:
        print('Invalid DATABASE_URL')
        
except ImportError:
    print('psycopg2 not installed. Using Flask ORM instead...')
    import sys
    from pathlib import Path
    import time
    
    sys.path.insert(0, str(Path.cwd()))
    os.environ['FLASK_ENV'] = 'production'
    
    from app import create_app
    from app.models.hospital import Hospital
    from app.extensions.database import db
    
    print('Starting Flask app (this may take 30 seconds)...')
    app = create_app('production')
    
    with app.app_context():
        ho = Hospital.query.filter_by(hospital_name='Head office').first()
        if ho:
            ho.allowed_radius_metres = 150
            db.session.commit()
            print(f'\n✅ SUCCESS:')
            print(f'   {ho.hospital_name}: {ho.allowed_radius_metres}m radius')
        else:
            print('\n❌ Head office not found')
