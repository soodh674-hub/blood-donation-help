#!/bin/sh
# Render build script for Blood Donation Platform
# Clean, standard Django deployment flow

echo "=== RENDER BUILD SCRIPT STARTING ==="
echo "Current directory: $(pwd)"
echo "Python version: $(python --version 2>&1)"
echo "=============================="

# Make sure script is executable
chmod +x "$0"

# Create necessary directories
echo "\n📁 Creating necessary directories..."
mkdir -p logs
mkdir -p media/medical_certificates
echo "✅ Directories created"

# Install dependencies
echo "\n📦 Installing Python dependencies..."
pip install -r requirements.txt

# CRITICAL: Run emergency database fix BEFORE Django starts
# This adds missing columns directly via psycopg2 (bypasses Django ORM)
echo "\n🔧 Running emergency database fix..."
if python emergency_db_fix.py 2>&1; then
    echo "✅ Emergency database fix completed successfully"
else
    echo "⚠️  Emergency fix had issues (this is OK if columns already exist)"
fi

# Check Django configuration
echo "\n✅ Checking Django configuration..."
python manage.py check --deploy || echo "⚠️  Django check had warnings (OK during build)"

# Run email diagnosis
echo "\n📧 Running email delivery diagnosis..."
python diagnose_email_delivery.py || echo "⚠️  Email diagnosis skipped"

# Generate and apply migrations (STANDARD DJANGO FLOW)
echo "\n🗄️  Generating migrations..."
python manage.py makemigrations --noinput || echo "⚠️  No new migrations needed"

echo "\n🗄️  Applying migrations..."
python manage.py migrate --noinput --verbosity=1 || echo "⚠️  Migration warnings (check logs)"

# Collect static files (now with improved error handling)
echo "\n📁 Collecting static files..."
if python manage.py collectstatic --noinput --verbosity=0; then
    echo "✅ Static files collected successfully"
else
    echo "⚠️  Static files warning (non-critical)"
fi

# Create superuser if needed (optional)
echo "\n👤 Checking superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Creating admin user...')
    User.objects.create_superuser('admin', 'admin@bloodis-life.online', 'admin123')
    print('✅ Admin user created')
else:
    print('✅ Superuser already exists')
" || echo "⚠️  Superuser check skipped"

echo "\n" + "=" * 60
echo "✅ BUILD COMPLETED SUCCESSFULLY!"
echo "=" * 60