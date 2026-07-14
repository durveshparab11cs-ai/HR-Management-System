"""
attendance/constants.py
========================
Attendance-specific constants and status values.
"""


class AttendanceStatus:
    PRESENT     = "present"
    ABSENT      = "absent"
    HALF_DAY    = "half_day"
    ON_LEAVE    = "on_leave"
    HOLIDAY     = "holiday"
    WEEKEND     = "weekend"
    WFH         = "work_from_home"


class LogAction:
    CHECK_IN          = "check_in"
    CHECK_OUT         = "check_out"
    REJECTED_CHECKIN  = "rejected_checkin"
    REJECTED_CHECKOUT = "rejected_checkout"


# Badge color mapping for templates
STATUS_BADGE_CLASS = {
    AttendanceStatus.PRESENT:  ("success",  "Present"),
    AttendanceStatus.ABSENT:   ("danger",   "Absent"),
    AttendanceStatus.HALF_DAY: ("warning",  "Half Day"),
    AttendanceStatus.ON_LEAVE: ("info",     "On Leave"),
    AttendanceStatus.HOLIDAY:  ("secondary","Holiday"),
    AttendanceStatus.WEEKEND:  ("light",    "Weekend"),
    AttendanceStatus.WFH:      ("primary",  "WFH"),
}
