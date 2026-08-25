"""
Temporary test endpoint to verify the API works.
This is a quick diagnostic tool - will be removed later.
"""

from flask import jsonify

def add_test_routes(coordinator_bp):
    """Add test routes to the coordinator blueprint"""
    
    @coordinator_bp.route("/test/diagnose", methods=["GET", "POST"])
    def test_diagnose():
        """Diagnostic endpoint to trace request handling"""
        from flask import request, g
        import logging
        
        logger = logging.getLogger("coordinator.test")
        
        logger.critical("=" * 70)
        logger.critical("🟢 TEST_DIAGNOSE CALLED")
        logger.critical("=" * 70)
        logger.critical(f"Method: {request.method}")
        logger.critical(f"Path: {request.path}")
        logger.critical(f"Full URL: {request.url}")
        logger.critical(f"g.skip_coordinator_auth: {getattr(g, 'skip_coordinator_auth', 'NOT SET')}")
        
        # Try to access current_user
        try:
            from flask_login import current_user
            logger.critical(f"current_user: {current_user}")
            logger.critical(f"current_user.is_authenticated: {current_user.is_authenticated}")
        except Exception as e:
            logger.critical(f"ERROR accessing current_user: {e}")
        
        logger.critical("=" * 70)
        
        return jsonify({
            "success": True,
            "message": "Diagnostic endpoint called",
            "path": request.path,
            "skip_auth": getattr(g, 'skip_coordinator_auth', False)
        })
