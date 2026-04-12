@echo off
REM ============================================
REM BloodLife - Database Migration Script
REM ============================================
REM This script will run all necessary migrations
REM for the new blood request tracking system
REM ============================================

echo.
echo ========================================
echo  BloodLife Migration Script
echo ========================================
echo.
echo Starting database migrations...
echo.

REM Navigate to project directory
cd /d "%~dp0"

echo Step 1/3: Creating migrations for blood_requests_app...
python manage.py makemigrations blood_requests_app
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to create migrations!
    echo Please check the error message above.
    pause
    exit /b 1
)

echo.
echo Step 2/3: Applying migrations to database...
python manage.py migrate blood_requests_app
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to apply migrations!
    echo Please check the error message above.
    pause
    exit /b 1
)

echo.
echo Step 3/3: Verifying migrations...
python manage.py showmigrations blood_requests_app
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Could not verify migrations!
    echo Please check manually.
)

echo.
echo ========================================
echo  Migration Complete!
echo ========================================
echo.
echo New models created:
echo   - RequestResponse
echo   - DonorLocationHistory
echo   - Enhanced BloodRequest fields
echo.
echo Next steps:
echo   1. Start Django server: python manage.py runserver
echo   2. Test the new API endpoints
echo   3. Continue with Phase 5-9 implementation
echo.
pause
