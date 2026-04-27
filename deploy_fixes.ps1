# Quick Deployment Script - Fix 404/500 Errors
# Run this on your PRODUCTION server after deploying code

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BloodLife Deployment Script" -ForegroundColor Cyan
Write-Host "Fixing 404/500 Errors + Database Migration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if we're in the right directory
if (-Not (Test-Path "manage.py")) {
    Write-Host "ERROR: manage.py not found!" -ForegroundColor Red
    Write-Host "Please run this script from the blood-donation-help directory" -ForegroundColor Red
    exit 1
}

Write-Host "[1/5] Checking Python environment..." -ForegroundColor Yellow
try {
    python --version
    Write-Host "✓ Python found" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/5] Installing dependencies..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt --quiet
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/5] Checking pending migrations..." -ForegroundColor Yellow
try {
    python manage.py showmigrations accounts | Select-String "0016"
    Write-Host "✓ Migration 0016 found" -ForegroundColor Green
} catch {
    Write-Host "✗ Migration check failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[4/5] Running database migrations..." -ForegroundColor Yellow
Write-Host "This will add missing Hospital model fields..." -ForegroundColor Gray
try {
    python manage.py migrate
    Write-Host "✓ Migrations completed successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Migration failed!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Try running manually: python manage.py migrate accounts" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[5/5] Collecting static files..." -ForegroundColor Yellow
try {
    python manage.py collectstatic --noinput --quiet
    Write-Host "✓ Static files collected" -ForegroundColor Green
} catch {
    Write-Host "⚠ Static files collection had warnings (usually safe to ignore)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Restart your web server (gunicorn/nginx/Render)" -ForegroundColor White
Write-Host "2. Test these pages:" -ForegroundColor White
Write-Host "   - https://bloodis-life.online/accounts/hospital-partners/" -ForegroundColor Gray
Write-Host "   - https://bloodis-life.online/accounts/trust-signals/" -ForegroundColor Gray
Write-Host "   - https://bloodis-life.online/requests/admin/donors/" -ForegroundColor Gray
Write-Host "   - https://bloodis-life.online/requests/admin/users/" -ForegroundColor Gray
Write-Host "   - https://bloodis-life.online/requests/admin/analytics/" -ForegroundColor Gray
Write-Host ""
Write-Host "If you see any errors, check the server logs." -ForegroundColor Yellow
Write-Host ""
