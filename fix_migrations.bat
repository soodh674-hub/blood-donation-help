@echo off
REM ============================================
REM BloodLife - Migration Fix Script (Batch)
REM Fixes: InconsistentMigrationHistory error
REM ============================================

echo.
echo ========================================
echo  BloodLife Migration Fix
echo ========================================
echo.
echo Fixing migration dependency issue...
echo.

REM Navigate to script directory
cd /d "%~dp0"

REM Step 1: Fake the initial migration
echo Step 1/3: Faking initial migration...
python manage.py migrate blood_requests_app 0001 --fake
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to fake migration!
    pause
    exit /b 1
)

echo.

REM Step 2: Create new migrations
echo Step 2/3: Creating new migrations...
python manage.py makemigrations blood_requests_app
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to create migrations!
    pause
    exit /b 1
)

echo.

REM Step 3: Apply all migrations
echo Step 3/3: Applying all migrations...
python manage.py migrate
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to apply migrations!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Migration Fixed Successfully!
echo ========================================
echo.
echo New models created:
echo   - RequestResponse
echo   - DonorLocationHistory
echo   - Enhanced BloodRequest fields
echo.
echo You can now continue with Phase 5-9!
echo.
pause
