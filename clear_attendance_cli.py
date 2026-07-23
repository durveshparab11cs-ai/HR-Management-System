"""
clear_attendance_cli.py
========================
Flask CLI command to clear ALL attendance data.

USAGE:
    flask clear-attendance --confirm

This will clear production database attendance immediately.
"""

import click
from flask.cli import with_appcontext
from app.extensions.database import db
from app.models.attendance import Attendance
from app.models.attendance_photo import AttendancePhoto
from app.models.attendance_log import AttendanceLog


@click.command('clear-attendance')
@click.option('--confirm', is_flag=True, help='Confirm deletion of all attendance data')
@with_appcontext
def clear_attendance_command(confirm):
    """Clear ALL attendance data from the database."""
    
    if not confirm:
        click.echo('❌ ERROR: You must use --confirm flag to proceed')
        click.echo('   Example: flask clear-attendance --confirm')
        return
    
    click.echo('=' * 70)
    click.echo('CLEARING ATTENDANCE DATA')
    click.echo('=' * 70)
    click.echo()
    
    # Count before deletion
    attendance_count = Attendance.query.count()
    photo_count = AttendancePhoto.query.count()
    log_count = AttendanceLog.query.count()
    
    click.echo(f'📊 Current Records:')
    click.echo(f'   - Attendance: {attendance_count}')
    click.echo(f'   - Photos: {photo_count}')
    click.echo(f'   - Logs: {log_count}')
    click.echo()
    
    if attendance_count == 0 and photo_count == 0 and log_count == 0:
        click.echo('✅ Attendance database is already empty!')
        return
    
    click.echo('🗑️  Deleting records...')
    click.echo()
    
    try:
        # Delete in correct order (foreign keys)
        if log_count > 0:
            click.echo(f'   Deleting {log_count} logs...')
            AttendanceLog.query.delete()
            db.session.commit()
            click.echo(f'   ✅ Deleted {log_count} logs')
        
        if photo_count > 0:
            click.echo(f'   Deleting {photo_count} photos...')
            AttendancePhoto.query.delete()
            db.session.commit()
            click.echo(f'   ✅ Deleted {photo_count} photos')
        
        if attendance_count > 0:
            click.echo(f'   Deleting {attendance_count} attendance records...')
            Attendance.query.delete()
            db.session.commit()
            click.echo(f'   ✅ Deleted {attendance_count} attendance')
        
        click.echo()
        click.echo('=' * 70)
        click.echo('✅ ATTENDANCE CLEARED SUCCESSFULLY!')
        click.echo('=' * 70)
        click.echo()
        click.echo('Verification:')
        click.echo(f'   - Attendance: {Attendance.query.count()}')
        click.echo(f'   - Photos: {AttendancePhoto.query.count()}')
        click.echo(f'   - Logs: {AttendanceLog.query.count()}')
        click.echo()
        
    except Exception as exc:
        db.session.rollback()
        click.echo()
        click.echo(f'❌ ERROR: {str(exc)}')
        click.echo()
        raise


def init_app(app):
    """Register the CLI command with Flask app."""
    app.cli.add_command(clear_attendance_command)
