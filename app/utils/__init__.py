"""
app/utils/__init__.py
======================
Utility layer — stateless, reusable helper functions.

Utils are pure functions with no Flask context dependency where possible.
They may be used by services, helpers, templates, and CLI commands alike.

Sub-modules:
    date_utils       — date/time parsing, formatting, arithmetic
    time_utils       — time-of-day helpers, shift calculations
    password_utils   — secure token generation, password policy checks
    file_utils       — file validation, path management, cleanup
    image_utils      — image resizing, thumbnail generation
    email_utils      — email composition and delivery helpers
    gps_utils        — coordinate distance, geofence checking
    response_utils   — standardized HTTP JSON response builders
    validation_utils — reusable input validators beyond WTForms
    pagination_utils — pagination metadata builders
    export_utils     — CSV, Excel, PDF export helpers
    string_utils     — slugify, truncate, sanitize helpers
"""
