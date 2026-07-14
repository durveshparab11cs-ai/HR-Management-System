#!/usr/bin/env bash
# ===========================================================================
# Smart HRMS — Pre-deployment Checklist Script
# ===========================================================================
# Run before deploying to production to verify critical configuration.
# Exits with code 1 if any critical check fails.
# ===========================================================================

set -euo pipefail

ERRORS=0

check() {
    local label="$1"
    local condition="$2"
    if eval "$condition"; then
        echo "  [PASS] $label"
    else
        echo "  [FAIL] $label"
        ERRORS=$((ERRORS + 1))
    fi
}

echo "============================================"
echo "  Smart HRMS — Production Readiness Check"
echo "============================================"
echo ""

echo "Environment:"
check "FLASK_ENV is production"     '[ "${FLASK_ENV:-}" = "production" ]'
check "SECRET_KEY is set"           '[ -n "${SECRET_KEY:-}" ]'
check "DATABASE_URL is set"         '[ -n "${DATABASE_URL:-}" ]'
check "MAIL_USERNAME is set"        '[ -n "${MAIL_USERNAME:-}" ]'
check "DEBUG is not True"           '[ "${FLASK_DEBUG:-0}" != "1" ]'

echo ""
echo "Security:"
check "SESSION_COOKIE_SECURE=True"  '[ "${SESSION_COOKIE_SECURE:-}" = "True" ]'
check "REMEMBER_COOKIE_SECURE=True" '[ "${REMEMBER_COOKIE_SECURE:-}" = "True" ]'
check "WTF_CSRF_ENABLED=True"       '[ "${WTF_CSRF_ENABLED:-True}" = "True" ]'

echo ""
echo "Files:"
check ".env NOT committed"          '! git ls-files --error-unmatch .env 2>/dev/null'
check "requirements/production.txt exists" '[ -f "requirements/production.txt" ]'
check "Dockerfile exists"           '[ -f "Dockerfile" ]'

echo ""
if [ "$ERRORS" -gt 0 ]; then
    echo "RESULT: $ERRORS check(s) FAILED. Resolve before deploying."
    exit 1
else
    echo "RESULT: All checks passed. Ready to deploy."
fi
