"""
app/blueprints/shift_change/forms.py
======================================
Forms for Shift Change Management
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import DateField, HiddenField, SelectField, StringField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Optional, ValidationError
import datetime


class ShiftChangeRequestForm(FlaskForm):
    """Employee shift change request form."""
    
    # Current shift (auto-filled, display only)
    current_shift_display = StringField("Current Shift", render_kw={"readonly": True})
    current_shift_id = HiddenField("Current Shift ID", validators=[DataRequired()])
    
    # Requested shift option 1: Select existing shift
    requested_shift_id = SelectField(
        "Select Predefined Shift (Optional)",
        coerce=int,
        validators=[Optional()],
        choices=[]
    )
    
    # Requested shift option 2: Custom timing
    requested_start_time = TimeField(
        "Requested Start Time",
        validators=[DataRequired()],
        format="%H:%M",
        render_kw={"placeholder": "09:00"}
    )
    
    requested_end_time = TimeField(
        "Requested End Time",
        validators=[DataRequired()],
        format="%H:%M",
        render_kw={"placeholder": "18:00"}
    )
    
    # Effective date
    effective_date = DateField(
        "Effective From Date",
        validators=[DataRequired()],
        format="%Y-%m-%d",
        render_kw={"min": datetime.date.today().isoformat()}
    )
    
    # Reason
    reason = TextAreaField(
        "Reason for Shift Change",
        validators=[DataRequired()],
        render_kw={"rows": 4, "placeholder": "Explain why you need this shift change..."}
    )
    
    # Attachment (optional)
    attachment = FileField(
        "Supporting Document (Optional)",
        validators=[FileAllowed(["pdf", "jpg", "jpeg", "png", "doc", "docx"], "Only PDF, images, or documents allowed")]
    )
    
    # Remarks
    remarks = TextAreaField(
        "Additional Remarks (Optional)",
        validators=[Optional()],
        render_kw={"rows": 2, "placeholder": "Any additional information..."}
    )
    
    def validate_requested_end_time(self, field):
        """Validate end time is after start time."""
        if self.requested_start_time.data and field.data:
            # For same-day shifts
            if field.data <= self.requested_start_time.data:
                # Allow overnight shifts only if explicitly intended
                if field.data == self.requested_start_time.data:
                    raise ValidationError("End time must be after start time")
    
    def validate_effective_date(self, field):
        """Validate effective date is not in the past."""
        if field.data and field.data < datetime.date.today():
            raise ValidationError("Effective date cannot be in the past")
    
    def validate_requested_shift_working_hours(self):
        """Validate working hours don't exceed maximum (e.g., 12 hours)."""
        if self.requested_start_time.data and self.requested_end_time.data:
            start = datetime.datetime.combine(datetime.date.today(), self.requested_start_time.data)
            end = datetime.datetime.combine(datetime.date.today(), self.requested_end_time.data)
            
            if end <= start:
                end += datetime.timedelta(days=1)
            
            total_hours = (end - start).total_seconds() / 3600
            
            # Maximum 14 hours including break
            if total_hours > 14:
                raise ValidationError("Shift duration cannot exceed 14 hours")


class ShiftChangeApprovalForm(FlaskForm):
    """Form for approving/rejecting shift change requests."""
    
    request_id = HiddenField("Request ID", validators=[DataRequired()])
    
    action = SelectField(
        "Action",
        choices=[
            ("approve", "Approve"),
            ("reject", "Reject"),
            ("return", "Return for Correction")
        ],
        validators=[DataRequired()]
    )
    
    remarks = TextAreaField(
        "Remarks",
        validators=[DataRequired()],
        render_kw={"rows": 3, "placeholder": "Enter your decision remarks..."}
    )


class ShiftChangeFilterForm(FlaskForm):
    """Filter form for shift change requests."""
    
    status = SelectField(
        "Status",
        choices=[
            ("", "All Status"),
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("returned", "Returned"),
            ("cancelled", "Cancelled")
        ],
        validators=[Optional()]
    )
    
    from_date = DateField(
        "From Date",
        validators=[Optional()],
        format="%Y-%m-%d"
    )
    
    to_date = DateField(
        "To Date",
        validators=[Optional()],
        format="%Y-%m-%d"
    )
    
    employee_code = StringField(
        "Employee Code",
        validators=[Optional()],
        render_kw={"placeholder": "E-XXXXXX"}
    )
