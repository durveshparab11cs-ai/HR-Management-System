# GPS Service Null Coordinate Fix

## Problem
Check-in endpoint was returning "System error occurred" because the GPS service was attempting to access `latitude`, `longitude`, and `radius_metres` attributes directly on office/hospital objects without null checks. If any of these attributes were missing or None, an `AttributeError` would be raised.

## Root Cause
In `gps_service.py`, after determining the reference point (hospital or office), the code directly accessed:
```python
reference_lat = reference_office.latitude
reference_lon = reference_office.longitude
allowed_radius = reference_office.radius_metres
```

If the object was partially hydrated or missing these attributes, this would crash with an AttributeError.

## Solution
Added three layers of protection:

### 1. Safe Attribute Access with getattr()
```python
reference_lat = getattr(reference_office, 'latitude', None)
reference_lon = getattr(reference_office, 'longitude', None)
allowed_radius = getattr(reference_office, 'radius_metres', None)
```

### 2. Coordinate Validation
Added explicit check that all required coordinates exist:
```python
if reference_lat is None or reference_lon is None or allowed_radius is None:
    reason = f"Office location incomplete: lat={reference_lat}, lon={reference_lon}, radius={allowed_radius}. Contact HR."
    logger.error("GPS_INVALID_COORDS | emp=%s | location=%s | lat=%s | lon=%s | radius=%s", ...)
    self._log(employee, None, None, None, None, action, reason)
    return GPSVerificationResult(success=False, error=reason)
```

### 3. Protected Logging Statements
Updated service.py to use getattr() for logging:
```python
logger.info("Office found: %s (radius=%sm)", 
           getattr(office, 'name', 'Unknown'), 
           getattr(office, 'radius_metres', 'Unknown'))
```

### 4. Protected Response Building
Updated `_build_gps_detail()` to safely access office attributes:
```python
"office_lat": getattr(office, 'latitude', None) if office else None,
"office_lon": getattr(office, 'longitude', None) if office else None,
"allowed_radius": getattr(office, 'radius_metres', None) if office else None,
```

## Files Modified
- `app/blueprints/attendance/gps_service.py` - Core GPS reference point logic
- `smart_hrms/app/blueprints/attendance/gps_service.py` - Mirror update
- `app/blueprints/attendance/service.py` - Logging and response building
- `smart_hrms/app/blueprints/attendance/service.py` - Mirror update

## Testing
To test the fix:
1. User attempts check-in with GPS coordinates
2. System should now gracefully handle missing office/hospital coordinates
3. If coordinates are incomplete, user receives: "Office location incomplete: lat=..., lon=..., radius=.... Contact HR."
4. Check-in endpoint no longer returns generic "System error occurred"

## Impact
- Check-in endpoint now handles missing/null office attributes gracefully
- Better error messages when office location is incomplete
- Prevents `AttributeError` exceptions from propagating to HTTP layer
- Improved logging for debugging configuration issues
