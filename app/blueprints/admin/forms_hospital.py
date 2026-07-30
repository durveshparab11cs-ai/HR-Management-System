"""
app/blueprints/admin/forms_hospital.py
=======================================
Forms for Hospital Management and Employee Allocation
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, FloatField, IntegerField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange, Length


class HospitalForm(FlaskForm):
    """Form for creating/editing hospitals."""
    
    hospital_name = StringField(
        'Hospital Name',
        validators=[DataRequired(), Length(max=200)],
        render_kw={'placeholder': 'e.g., AIIMS Hospital (Gorakhpur)'}
    )
    
    hospital_code = StringField(
        'Hospital Code',
        validators=[Optional(), Length(max=50)],
        render_kw={'placeholder': 'e.g., HQ-001'}
    )
    
    location = StringField(
        'Location',
        validators=[Optional(), Length(max=200)],
        render_kw={'placeholder': 'e.g., Gorakhpur, Mumbai'}
    )
    
    address = TextAreaField(
        'Full Address',
        validators=[Optional(), Length(max=500)],
        render_kw={'rows': 3, 'placeholder': 'Complete address'}
    )
    
    city = StringField(
        'City',
        validators=[Optional(), Length(max=100)],
        render_kw={'placeholder': 'e.g., Mumbai'}
    )
    
    state = StringField(
        'State',
        validators=[Optional(), Length(max=100)],
        render_kw={'placeholder': 'e.g., Maharashtra'}
    )
    
    latitude = FloatField(
        'Latitude',
        validators=[DataRequired(), NumberRange(min=-90, max=90)],
        render_kw={'placeholder': 'e.g., 18.520430', 'step': '0.000001'}
    )
    
    longitude = FloatField(
        'Longitude',
        validators=[DataRequired(), NumberRange(min=-180, max=180)],
        render_kw={'placeholder': 'e.g., 73.856743', 'step': '0.000001'}
    )
    
    allowed_radius_metres = IntegerField(
        'Allowed GPS Radius (metres)',
        validators=[DataRequired(), NumberRange(min=10, max=10000)],
        default=100,
        render_kw={'placeholder': '100'}
    )
    
    is_active = BooleanField(
        'Active',
        default=True
    )
    
    status = SelectField(
        'Status',
        choices=[
            ('Active', 'Active'),
            ('Inactive', 'Inactive'),
        ],
        default='Active'
    )


class HospitalImportForm(FlaskForm):
    """Form for importing hospitals from Excel."""
    
    file = FileField(
        'Excel File',
        validators=[
            DataRequired(),
            FileAllowed(['xlsx', 'xls'], 'Only Excel files (.xlsx, .xls) are allowed')
        ]
    )


class EmployeeAllocationImportForm(FlaskForm):
    """Form for importing employee allocations from Excel."""
    
    file = FileField(
        'Excel File (Employee Master)',
        validators=[
            DataRequired(),
            FileAllowed(['xlsx', 'xls'], 'Only Excel files (.xlsx, .xls) are allowed')
        ]
    )


class HospitalSearchForm(FlaskForm):
    """Form for searching hospitals."""
    
    search_query = StringField(
        'Search',
        validators=[Optional()],
        render_kw={'placeholder': 'Search by name, code, or location...'}
    )
    
    status_filter = SelectField(
        'Status',
        choices=[
            ('', 'All'),
            ('Active', 'Active'),
            ('Inactive', 'Inactive'),
        ],
        default=''
    )
