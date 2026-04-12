# ============================================
# BloodLife - Database Migration Script (PowerShell)
# ============================================
# This script will run all necessary migrations
# for the new blood request tracking system
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " BloodLife Migration Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting database migrations..." -ForegroundColor Yellow
Write-Host ""

# Navigate to script directory
Set-Location $PSScriptRoot

# Step 1: Create migrations
Write-Host "Step 1/3: Creating migrations for blood_requests_app..." -ForegroundColor Green
python manage.py makemigrations blood_requests_app
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to create migrations!" -ForegroundColor Red
    Write-Host "Please check the error message above." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Step 2: Apply migrations
Write-Host "Step 2/3: Applying migrations to database..." -ForegroundColor Green
python manage.py migrate blood_requests_app
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to apply migrations!" -ForegroundColor Red
    Write-Host "Please check the error message above." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Step 3: Verify migrations
Write-Host "Step 3/3: Verifying migrations..." -ForegroundColor Green
python manage.py showmigrations blood_requests_app
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "WARNING: Could not verify migrations!" -ForegroundColor Yellow
    Write-Host "Please check manually." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Migration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "New models created:" -ForegroundColor White
Write-Host "  ✓ RequestResponse" -ForegroundColor Green
Write-Host "  ✓ DonorLocationHistory" -ForegroundColor Green
Write-Host "  ✓ Enhanced BloodRequest fields" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Start Django server: python manage.py runserver" -ForegroundColor White
Write-Host "  2. Test the new API endpoints" -ForegroundColor White
Write-Host "  3. Continue with Phase 5-9 implementation" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
