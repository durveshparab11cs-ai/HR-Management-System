#!/usr/bin/env python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

_db_path = r"sqlite:///c:\Users\durve\Downloads\HR management system\smart_hrms\instance\smart_hrms_dev.db"
_db_url = os.environ.get("DATABASE_URL", _db_path)

engine = create_engine(_db_url)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Update E-2512012
    session.execute(
        text("UPDATE users SET role = 'super_admin' WHERE id IN (SELECT user_id FROM employees WHERE employee_code = 'E-2512012')")
    )
    session.commit()
    
    # Update E-2603025
    session.execute(
        text("UPDATE users SET role = 'super_admin' WHERE id IN (SELECT user_id FROM employees WHERE employee_code = 'E-2603025')")
    )
    session.commit()
    
    # Verify
    result = session.execute(
        text("SELECT e.employee_code, u.role FROM users u INNER JOIN employees e ON u.id = e.user_id WHERE e.employee_code IN ('E-2512012', 'E-2603025')")
    ).fetchall()
    
    print("✅ Updated roles:")
    for code, role in result:
        print(f"  {code}: {role}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
