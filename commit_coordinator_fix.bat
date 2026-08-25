@echo off
cd /d "%~dp0"
echo Checking git status...
git status

echo.
echo Adding coordinator files...
git add app/blueprints/coordinator/routes.py
git add app/blueprints/coordinator/templates/coordinator/portal.html

echo.
echo Committing changes...
git commit -m "Fix: Coordinator Portal API returning JSON instead of HTML

- Bypass Flask-Login for public kiosk API endpoints
- Register routes directly with Flask app
- Add @csrf.exempt to API endpoints
- Correct API endpoint URLs in frontend
- Add /coordinator/portal route to serve portal page
- All API responses now return valid JSON

API endpoints:
- POST /coordinator/api/search-employee
- POST /coordinator/api/submit-attendance
- POST /coordinator/api/get-gps
- GET /coordinator/portal

Employee search workflow now works: code entry -> API search -> camera -> attendance submission"

echo.
echo Pushing to remote...
git push -u origin main

echo.
echo Done!
pause
