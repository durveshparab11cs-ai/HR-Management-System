#!/usr/bin/env python3
"""
Database Initialization Script - MUST RUN BEFORE APP STARTUP
===============================================================
This script ensures:
1. All 30+ database tables are created
2. Default OfficeSettings record exists
3. Critical leave types exist
4. App will not crash on first request

Run this BEFORE starting gunicorn on Render.
"""

import os
import sys
import logging

# Add current directory to Python path so imports work from any location
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Set production environment
os.environ['FLASK_ENV'] = 'production'

logger.info("=" * 80)
logger.info("DATABASE INITIALIZATION - RENDER DEPLOYMENT")
logger.info("=" * 80)

try:
    # Import app factory
    logger.info("[1/5] Importing app factory...")
    from app import create_app
    logger.info("[1/5] SUCCESS - app factory imported")
    
    # Create app
    logger.info("[2/5] Creating Flask application...")
    app = create_app('production')
    logger.info("[2/5] SUCCESS - Flask app created")
    
    # Initialize database
    logger.info("[3/5] Creating database tables...")
    with app.app_context():
        from app.extensions.database import db
        from sqlalchemy import inspect
        
        # Create all tables
        db.create_all()
        logger.info("[3/5] SUCCESS - db.create_all() executed")
        
        # Verify tables were created
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        logger.info(f"[3/5] Database has {len(tables)} tables:")
        for table in sorted(tables):
            logger.info(f"      - {table}")
        
        # Check critical tables
        critical = ['office_settings', 'employees', 'attendance', 'users']
        missing = [t for t in critical if t not in tables]
        if missing:
            logger.error(f"[3/5] CRITICAL: Missing tables: {missing}")
            sys.exit(1)
        
        # Ensure OfficeSettings exists
        logger.info("[4/5] Seeding OfficeSettings...")
        try:
            from app.models.office_settings import OfficeSettings
            import datetime
            
            existing = OfficeSettings.query.first()
            if not existing:
                logger.info("      Creating default 'Head Office'...")
                office = OfficeSettings(
                    name="Head Office",
                    is_default=True,
                    latitude=18.520430,
                    longitude=73.856743,
                    radius_metres=100,
                    office_start_time=datetime.time(9, 0),
                    office_end_time=datetime.time(18, 0),
                    grace_period_minutes=10,
                    half_day_threshold_minutes=300,
                )
                db.session.add(office)
                db.session.commit()
                logger.info("      SUCCESS - OfficeSettings created")
            else:
                logger.info(f"      OfficeSettings already exists: {existing.name}")
        except Exception as e:
            logger.error(f"[4/5] FAILED to seed OfficeSettings: {e}")
            db.session.rollback()
        
        # Ensure LeaveTypes exist
        logger.info("[4/5] Seeding LeaveTypes...")
        try:
            from app.models.leave import LeaveType
            
            leave_types_needed = {
                'Casual Leave': 'CL',
                'Sick Leave': 'SL',
                'Paid Leave': 'PL',
                'Loss of Pay': 'LOP',
                'Comp Off': 'CO',
            }
            
            for name, code in leave_types_needed.items():
                existing = LeaveType.query.filter_by(code=code).first()
                if not existing:
                    logger.info(f"      Creating {name} ({code})...")
                    lt = LeaveType(
                        name=name,
                        code=code,
                        max_days_per_year=12,
                        is_paid=True,
                        color='#3b82f6'
                    )
                    db.session.add(lt)
            
            db.session.commit()
            logger.info("      SUCCESS - LeaveTypes checked/created")
        except Exception as e:
            logger.error(f"[4/5] FAILED to seed LeaveTypes: {e}")
            db.session.rollback()
        
        logger.info("[4/5] SUCCESS - Database seeding complete")
    
    logger.info("[5/5] Health check...")
    with app.test_client() as client:
        response = client.get('/health')
        if response.status_code == 200:
            logger.info("[5/5] SUCCESS - Health endpoint returns 200")
        else:
            logger.error(f"[5/5] FAILED - Health endpoint returns {response.status_code}")
            sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("DATABASE INITIALIZATION COMPLETE - APP READY")
    logger.info("=" * 80)
    sys.exit(0)

except Exception as e:
    logger.error("=" * 80)
    logger.error(f"INITIALIZATION FAILED: {e}")
    logger.error("=" * 80)
    import traceback
    traceback.print_exc()
    sys.exit(1)
