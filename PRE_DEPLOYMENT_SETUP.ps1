# ========================================
# BloodLife - Pre-Deployment Setup Script
# Run this BEFORE deploying to Render
# ========================================

Write-Host "================================" -ForegroundColor Cyan
Write-Host "BloodLife Pre-Deployment Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonCmd = $null

# Try different Python commands
$pythonCommands = @("python", "python3", "py", "py -3")
foreach ($cmd in $pythonCommands) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            Write-Host "✓ Python found: $version" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-Host "✗ ERROR: Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.10+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "During installation, CHECK 'Add Python to PATH'" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 1: Installing Dependencies" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
& $pythonCmd -m pip install --upgrade pip setuptools wheel
& $pythonCmd -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ ERROR: Failed to install dependencies!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 2: Creating Necessary Directories" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
$directories = @(
    "logs",
    "media",
    "media/medical_certificates",
    "media/profile_photos",
    "static",
    "static/css",
    "static/js",
    "static/images"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "✓ Exists: $dir" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Step 3: Checking Environment Variables" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Check if .env file exists
if (Test-Path ".env") {
    Write-Host "✓ .env file found" -ForegroundColor Green
    
    # Read .env and check for critical variables
    $envContent = Get-Content ".env"
    $requiredVars = @("SECRET_KEY", "DEBUG")
    $missingVars = @()
    
    foreach ($var in $requiredVars) {
        if ($envContent -match "^$var=") {
            Write-Host "✓ $var is set" -ForegroundColor Green
        } else {
            Write-Host "✗ $var is missing!" -ForegroundColor Red
            $missingVars += $var
        }
    }
    
    if ($missingVars.Count -gt 0) {
        Write-Host ""
        Write-Host "WARNING: Missing critical environment variables!" -ForegroundColor Yellow
        Write-Host "Please add them to your .env file" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ .env file not found!" -ForegroundColor Red
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ Created .env file - PLEASE EDIT IT WITH YOUR VALUES!" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Step 4: Making Migrations" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
& $pythonCmd manage.py makemigrations --noinput

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ Some migrations may have issues, but continuing..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 5: Applying Migrations" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan
& $pythonCmd manage.py migrate --noinput

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ ERROR: Migration failed!" -ForegroundColor Red
    Write-Host "Please check the error messages above" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 6: Collecting Static Files" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
& $pythonCmd manage.py collectstatic --noinput --clear

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ Static files collection had issues" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 7: Creating Superuser (Optional)" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Do you want to create a superuser (admin account)?" -ForegroundColor Yellow
$createSuper = Read-Host "Type 'yes' to create, or press Enter to skip"

if ($createSuper -eq "yes") {
    & $pythonCmd manage.py createsuperuser
}

Write-Host ""
Write-Host "Step 8: Testing Local Server" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host "Starting development server for testing..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server when done testing" -ForegroundColor Yellow
Write-Host ""
Write-Host "Server will start at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host ""

# Start the server
& $pythonCmd manage.py runserver

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your application is now ready for Render deployment!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Test your application locally at http://127.0.0.1:8000" -ForegroundColor White
Write-Host "2. Fix any errors you find" -ForegroundColor White
Write-Host "3. Push to GitHub" -ForegroundColor White
Write-Host "4. Deploy to Render" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
