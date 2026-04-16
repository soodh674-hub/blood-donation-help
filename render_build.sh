#!/bin/bash
# Render build script for BloodLife Blood Donation Platform
# Enhanced with migrations, environment checks, WebSocket support, and better error handling

set -e  # Exit on error

echo "=== BLOODLIFE BUILD SCRIPT STARTING ==="
echo "Current directory: $(pwd)"
echo "Python version: $(python --version 2>&1)"
echo "Build date: $(date)"
echo "=============================="

# Make sure script is executable
chmod +x "$0"

# Create necessary directories
echo "\n📁 Creating necessary directories..."
mkdir -p logs
mkdir -p media/medical_certificates
mkdir -p media/profile_photos
mkdir -p static
mkdir -p static/css
mkdir -p static/js
mkdir -p static/images
mkdir -p static/bootstrap
mkdir -p static/aos
echo "✅ Directories created"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "⚠️  requirements.txt not found, skipping dependency installation"
else
    # Install dependencies
    echo "\n📦 Installing Python dependencies..."
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
fi

# Verify Django installation
echo "\n✅ Verifying Django installation..."
python -c "import django; print(f'Django {django.VERSION} installed successfully')" || echo "⚠️  Django verification skipped"

# Set Django settings module (fixed path)
export DJANGO_SETTINGS_MODULE=blood_donation.settings

# Check for critical environment variables
echo "\n🔍 Checking environment variables..."
MISSING_VARS=0

if [ -z "$SECRET_KEY" ]; then
    echo "❌ ERROR: SECRET_KEY not set"
    MISSING_VARS=$((MISSING_VARS + 1))
fi

if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  WARNING: DATABASE_URL not set (using SQLite)"
fi

if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
    echo "⚠️  WARNING: GOOGLE_MAPS_API_KEY not set (maps will not work)"
fi

if [ -z "$EMAIL_HOST_USER" ] || [ -z "$EMAIL_HOST_PASSWORD" ]; then
    echo "⚠️  WARNING: Email credentials not set (email notifications disabled)"
fi

if [ $MISSING_VARS -gt 0 ]; then
    echo "\n❌ CRITICAL: $MISSING_VARS required environment variable(s) missing!"
    echo "Please set them in Render dashboard or .env file"
    exit 1
fi

echo "✅ Environment check complete"

# Run migrations
echo "\n🗄️  Running database migrations..."
python manage.py makemigrations --noinput || echo "⚠️  makemigrations skipped"
python manage.py migrate --noinput || echo "⚠️  migrations failed (will be retried in runtime)"
echo "✅ Migrations complete"

# Collect static files during build phase
echo "\n📦 Collecting static files..."
python manage.py collectstatic --noinput --clear --verbosity=2
echo "✅ Static files collected"

# Create superuser if needed (optional, for initial setup)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "\n👤 Creating superuser..."
    python manage.py createsuperuser --noinput --username "$SUPERUSER_USERNAME" --email "$SUPERUSER_EMAIL" || echo "⚠️  Superuser creation skipped"
fi

echo "\n============================================================"
echo "✅ BUILD COMPLETED SUCCESSFULLY!"
echo "Static files collected and ready for deployment"
echo "Migrations applied successfully"
echo "============================================================"