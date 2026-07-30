"""
app/services/employee_allocation_service.py
============================================
Service for allocating employees to hospitals and shifts via Excel import
"""

import datetime
import os
import re
from typing import Tuple, Dict, Optional
import pandas as pd
from flask import current_app
from werkzeug.utils import secure_filename

from app.extensions.database import db
from app.models.employee import Employee
from app.models.employee_master import EmployeeMaster
from app.models.hospital import Hospital


class EmployeeAllocationService:
    """Service for employee hospital and shift allocation."""
    
    def parse_shift_timing(self, shift_str: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse shift timing string to extract start and end times.
        
        Examples:
            "10:00 AM to 7:00 PM" -> ("10:00 AM", "07:00 PM")
            "9:00 AM to 6:00 PM" -> ("09:00 AM", "06:00 PM")
            "Flexible Shift" -> (None, None)
            
        Returns:
            (start_time, end_time) or (None, None) if flexible
        """
        if not shift_str or pd.isna(shift_str):
            return None, None
        
        shift_str = str(shift_str).strip()
        
        # Check for flexible shift
        if 'flexible' in shift_str.lower():
            return None, None
        
        # Try to parse time range
        # Pattern: "HH:MM AM/PM to HH:MM AM/PM"
        pattern = r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s*(?:to|-)\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))'
        match = re.search(pattern, shift_str, re.IGNORECASE)
        
        if match:
            start_time = match.group(1).strip().upper()
            end_time = match.group(2).strip().upper()
            
            # Normalize format (ensure space before AM/PM)
            start_time = re.sub(r'(\d{1,2}:\d{2})\s*(AM|PM)', r'\1 \2', start_time)
            end_time = re.sub(r'(\d{1,2}:\d{2})\s*(AM|PM)', r'\1 \2', end_time)
            
            # Pad single digit hours
            start_time = re.sub(r'^(\d):', r'0\1:', start_time)
            end_time = re.sub(r'^(\d):', r'0\1:', end_time)
            
            return start_time, end_time
        
        return None, None
    
    def determine_shift_name(self, start_time: str, end_time: str) -> str:
        """
        Determine shift name based on timings.
        
        Returns:
            Shift name like "Morning Shift", "Evening Shift", "Night Shift"
        """
        if not start_time or not end_time:
            return "General Shift"
        
        try:
            # Extract hour from start time
            hour_match = re.match(r'(\d{1,2}):', start_time)
            if not hour_match:
                return "General Shift"
            
            hour = int(hour_match.group(1))
            
            # Check AM/PM
            if 'PM' in start_time.upper():
                if hour != 12:
                    hour += 12
            elif 'AM' in start_time.upper() and hour == 12:
                hour = 0
            
            # Classify shift
            if 5 <= hour < 12:
                return "Morning Shift"
            elif 12 <= hour < 17:
                return "Afternoon Shift"
            elif 17 <= hour < 21:
                return "Evening Shift"
            else:
                return "Night Shift"
                
        except:
            return "General Shift"
    
    def import_employee_allocations_from_excel(
        self,
        file,
        imported_by_user_id: int
    ) -> Tuple[bool, str, Dict]:
        """
        Import employee hospital and shift allocations from Excel.
        
        Args:
            file: FileStorage object
            imported_by_user_id: User ID who is importing
            
        Returns:
            (success, message, statistics)
        """
        start_time = datetime.datetime.now()
        
        stats = {
            'total_rows': 0,
            'employees_updated': 0,
            'employees_not_found': 0,
            'hospitals_not_found': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            temp_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'instance/uploads'), filename)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            file.save(temp_path)
            
            # Read Excel
            df = pd.read_excel(temp_path)
            stats['total_rows'] = len(df)
            
            current_app.logger.info(f"Processing {stats['total_rows']} employee allocations from Excel")
            
            # Get all hospitals for quick lookup
            hospitals = {h.hospital_name: h for h in Hospital.query.filter_by(is_deleted=False).all()}
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    row_num = index + 2  # Excel row number
                    
                    # Get employee code
                    emp_code = str(row.get('EMP-CODE', '')).strip()
                    if not emp_code or emp_code == 'nan':
                        stats['errors'].append(f"Row {row_num}: Employee code missing")
                        stats['failed'] += 1
                        continue
                    
                    # Find employee by code
                    employee = Employee.query.join(Employee.user).filter(
                        Employee.employee_code == emp_code
                    ).first()
                    
                    if not employee:
                        stats['errors'].append(f"Row {row_num}: Employee {emp_code} not found")
                        stats['employees_not_found'] += 1
                        stats['failed'] += 1
                        continue
                    
                    # Get hospital/location
                    location = str(row.get('WORKING LOCATION', '')).strip()
                    if location == 'nan' or not location:
                        stats['errors'].append(f"Row {row_num}: {emp_code} - Working location missing")
                        stats['failed'] += 1
                        continue
                    
                    # Find matching hospital
                    hospital = None
                    
                    # Try exact match first
                    if location in hospitals:
                        hospital = hospitals[location]
                    else:
                        # Try partial match
                        for hosp_name, hosp in hospitals.items():
                            if location.lower() in hosp_name.lower() or hosp_name.lower() in location.lower():
                                hospital = hosp
                                break
                    
                    if not hospital:
                        stats['errors'].append(f"Row {row_num}: {emp_code} - Hospital '{location}' not found")
                        stats['hospitals_not_found'] += 1
                        stats['failed'] += 1
                        continue
                    
                    # Get shift timing
                    shift_timing = str(row.get('full Shift timing', '')).strip()
                    start_time, end_time = self.parse_shift_timing(shift_timing)
                    
                    # Determine if flexible shift
                    working_status = str(row.get('WORKING STATUS', '')).strip().lower()
                    is_flexible = 'flexible' in shift_timing.lower() or 'flexible' in working_status
                    
                    # Get shift name
                    if is_flexible:
                        shift_name = "Flexible Shift"
                    elif start_time and end_time:
                        shift_name = self.determine_shift_name(start_time, end_time)
                    else:
                        shift_name = "General Shift"
                    
                    # Update employee
                    employee.hospital_id = hospital.id
                    employee.current_shift = shift_name
                    employee.shift_start_time = start_time
                    employee.shift_end_time = end_time
                    employee.is_flexible_shift = 1 if is_flexible else 0
                    employee.required_working_hours = 9  # Default 9 hours
                    
                    # Update branch if available
                    if location:
                        employee.branch = location
                    
                    stats['employees_updated'] += 1
                    
                    if stats['employees_updated'] % 100 == 0:
                        current_app.logger.info(f"Processed {stats['employees_updated']} employees...")
                    
                except Exception as e:
                    stats['errors'].append(f"Row {row_num}: {str(e)}")
                    stats['failed'] += 1
                    continue
            
            # Commit all changes
            db.session.commit()
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
            # Log import
            duration = (datetime.datetime.now() - start_time).total_seconds()
            self._log_import(
                import_type='employee_allocation',
                imported_by=imported_by_user_id,
                filename=filename,
                stats=stats,
                duration=duration
            )
            
            message = f"Allocation completed: {stats['employees_updated']} updated, {stats['failed']} failed"
            if stats['employees_not_found'] > 0:
                message += f" ({stats['employees_not_found']} employees not found)"
            if stats['hospitals_not_found'] > 0:
                message += f" ({stats['hospitals_not_found']} hospitals not found)"
            
            return True, message, stats
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error importing employee allocations: {str(e)}")
            return False, f"Import failed: {str(e)}", stats
    
    def _log_import(self, import_type: str, imported_by: int, filename: str, stats: Dict, duration: float):
        """Log import operation to database."""
        try:
            from sqlalchemy import text
            
            error_log = "\n".join(stats.get('errors', []))[:5000]  # Limit to 5000 chars
            
            db.session.execute(text("""
                INSERT INTO import_logs (
                    import_type, imported_by, filename,
                    total_rows, rows_imported, rows_updated, rows_failed,
                    employees_updated,
                    status, error_log, duration_seconds
                ) VALUES (
                    :type, :user, :file,
                    :total, :imported, :updated, :failed,
                    :emp_upd,
                    :status, :errors, :duration
                )
            """), {
                'type': import_type,
                'user': imported_by,
                'file': filename,
                'total': stats.get('total_rows', 0),
                'imported': 0,
                'updated': stats.get('employees_updated', 0),
                'failed': stats.get('failed', 0),
                'emp_upd': stats.get('employees_updated', 0),
                'status': 'completed' if stats.get('failed', 0) == 0 else 'partial',
                'errors': error_log,
                'duration': duration
            })
            
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error logging import: {str(e)}")
    
    def get_employee_allocation_stats(self) -> Dict:
        """
        Get statistics about employee allocations.
        
        Returns:
            Dict with allocation statistics
        """
        try:
            total_employees = Employee.query.count()
            allocated = Employee.query.filter(Employee.hospital_id.isnot(None)).count()
            unallocated = total_employees - allocated
            flexible = Employee.query.filter_by(is_flexible_shift=1).count()
            fixed = allocated - flexible
            
            return {
                'total_employees': total_employees,
                'allocated': allocated,
                'unallocated': unallocated,
                'flexible_shift': flexible,
                'fixed_shift': fixed
            }
        except Exception as e:
            current_app.logger.error(f"Error getting allocation stats: {str(e)}")
            return {}
