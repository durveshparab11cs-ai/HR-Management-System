"""
app/utils/jwt_utils.py
=======================
JWT token generation and validation utilities for API authentication.

Provides functions to create and verify JWT tokens for mobile API access.
"""

import datetime
from typing import Optional, Tuple
import jwt
from flask import current_app, request
from functools import wraps

from app.models.user import User


def generate_access_token(user_id: int, employee_code: str = None) -> str:
    """
    Generate a JWT access token for API authentication.
    
    Args:
        user_id: User's database ID
        employee_code: Optional employee code
    
    Returns:
        JWT token string
    """
    payload = {
        'user_id': user_id,
        'employee_code': employee_code,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),  # 24 hours
        'iat': datetime.datetime.utcnow(),
        'type': 'access'
    }
    
    secret_key = current_app.config.get('SECRET_KEY')
    return jwt.encode(payload, secret_key, algorithm='HS256')


def generate_refresh_token(user_id: int) -> str:
    """
    Generate a JWT refresh token for token renewal.
    
    Args:
        user_id: User's database ID
    
    Returns:
        JWT refresh token string
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30),  # 30 days
        'iat': datetime.datetime.utcnow(),
        'type': 'refresh'
    }
    
    secret_key = current_app.config.get('SECRET_KEY')
    return jwt.encode(payload, secret_key, algorithm='HS256')


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload dict or None if invalid
    """
    try:
        secret_key = current_app.config.get('SECRET_KEY')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_token_from_header() -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    
    Returns:
        Token string or None if not found
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    # Format: "Bearer <token>"
    parts = auth_header.split()
    
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def get_current_user_from_token() -> Tuple[bool, Optional[User], Optional[str]]:
    """
    Get current user from JWT token in request header.
    
    Returns:
        Tuple of (success, user, error_message)
    """
    token = get_token_from_header()
    
    if not token:
        return False, None, "No authorization token provided"
    
    payload = decode_token(token)
    
    if not payload:
        return False, None, "Invalid or expired token"
    
    if payload.get('type') != 'access':
        return False, None, "Invalid token type"
    
    user_id = payload.get('user_id')
    
    if not user_id:
        return False, None, "Invalid token payload"
    
    user = User.query.get(user_id)
    
    if not user:
        return False, None, "User not found"
    
    if user.is_deleted:
        return False, None, "User account is deleted"
    
    if user.status != 'active':
        return False, None, "User account is not active"
    
    return True, user, None


def jwt_required(f):
    """
    Decorator to require JWT authentication for API endpoints.
    
    Usage:
        @api_bp.route('/protected')
        @jwt_required
        def protected_route():
            user = g.current_user
            return success_response(data={'user_id': user.id})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import g
        from app.utils.response_utils import unauthorized_response
        
        success, user, error_msg = get_current_user_from_token()
        
        if not success:
            return unauthorized_response(message=error_msg or "Authentication required")
        
        # Store user in Flask's g object for access in route
        g.current_user = user
        g.user_id = user.id
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_jwt(f):
    """
    Decorator for optional JWT authentication.
    Sets g.current_user if valid token is provided, but doesn't require it.
    
    Usage:
        @api_bp.route('/public-or-private')
        @optional_jwt
        def route():
            if hasattr(g, 'current_user'):
                # User is authenticated
                return success_response(data={'user': g.current_user.id})
            else:
                # Public access
                return success_response(data={'message': 'Public data'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import g
        
        success, user, _ = get_current_user_from_token()
        
        if success and user:
            g.current_user = user
            g.user_id = user.id
        
        return f(*args, **kwargs)
    
    return decorated_function


def refresh_access_token(refresh_token: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Generate new access token from refresh token.
    
    Args:
        refresh_token: JWT refresh token
    
    Returns:
        Tuple of (success, new_access_token, error_message)
    """
    payload = decode_token(refresh_token)
    
    if not payload:
        return False, None, "Invalid or expired refresh token"
    
    if payload.get('type') != 'refresh':
        return False, None, "Invalid token type"
    
    user_id = payload.get('user_id')
    
    if not user_id:
        return False, None, "Invalid token payload"
    
    user = User.query.get(user_id)
    
    if not user or user.is_deleted or user.status != 'active':
        return False, None, "Invalid user"
    
    # Get employee code if available
    from app.models.employee import Employee
    employee = Employee.query.filter_by(user_id=user_id, is_deleted=False).first()
    employee_code = employee.employee_code if employee else None
    
    # Generate new access token
    new_access_token = generate_access_token(user_id, employee_code)
    
    return True, new_access_token, None
