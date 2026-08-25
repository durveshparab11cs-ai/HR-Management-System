"""
Test to verify coordinator API returns JSON instead of 302 redirect
by checking the route decorator configuration.
"""

import inspect
from app.blueprints.coordinator.routes import api_search_employee, public_api

print("=" * 70)
print("API ENDPOINT STATUS CHECK")
print("=" * 70)
print()

# Check if the function has the public_api decorator
print(f"Function name: {api_search_employee.__name__}")
print()

# Check for is_public_api attribute
has_is_public_api = hasattr(api_search_employee, 'is_public_api')
is_public_api_value = getattr(api_search_employee, 'is_public_api', None)

print(f"Has 'is_public_api' attribute: {has_is_public_api}")
print(f"Value of 'is_public_api': {is_public_api_value}")
print()

# Check for requires_auth attribute  
has_requires_auth = hasattr(api_search_employee, 'requires_auth')
requires_auth_value = getattr(api_search_employee, 'requires_auth', None)

print(f"Has 'requires_auth' attribute: {has_requires_auth}")
print(f"Value of 'requires_auth': {requires_auth_value}")
print()

# Print the source code
print("=" * 70)
print("FUNCTION SOURCE:")
print("=" * 70)
print()
print(inspect.getsource(api_search_employee))
print()

print("=" * 70)
print("CONCLUSION:")
print("=" * 70)
if is_public_api_value and not requires_auth_value:
    print("✅ Route is properly decorated with @public_api")
    print("✅ This means it should NOT require authentication")
    print("✅ API should return JSON response (200) not 302 redirect")
else:
    print("❌ Route may not have proper @public_api decoration")
    print(f"   is_public_api: {is_public_api_value}")
    print(f"   requires_auth: {requires_auth_value}")
