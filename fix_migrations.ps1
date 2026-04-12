# ============================================
# BloodLife - Migration Fix Script
# Fixes: InconsistentMigrationHistory error
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " BloodLife Migration Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Fixing migration dependency issue..." -ForegroundColor Yellow
Write-Host ""

# Navigate to script directory
Set-Location $PSScriptRoot

# Step 1: Fake the initial migration
Write-Host "Step 1/3: Faking initial migration..." -ForegroundColor Green
python manage.py migrate blood_requests_app 0001 --fake
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to fake migration!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Step 2: Create new migrations
Write-Host "Step 2/3: Creating new migrations..." -ForegroundColor Green
python manage.py makemigrations blood_requests_app
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to create migrations!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Step 3: Apply all migrations
Write-Host "Step 3/3: Applying all migrations..." -ForegroundColor Green
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to apply migrations!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Migration Fixed Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "New models created:" -ForegroundColor White
Write-Host "  ✓ RequestResponse" -ForegroundColor Green
Write-Host "  ✓ DonorLocationHistory" -ForegroundColor Green
Write-Host "  ✓ Enhanced BloodRequest fields" -ForegroundColor Green
Write-Host ""
Write-Host "You can now continue with Phase 5-9!" -ForegroundColor Yellow
Write-Host ""

Read-Host "Press Enter to exit"
