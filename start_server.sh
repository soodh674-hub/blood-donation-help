#!/bin/bash
# Start script with better error handling and logging

echo "=== STARTING DJANGO SERVER ==="
echo "Date: $(date)"
echo "Python: $(python --version 2>&1)"
echo "Working directory: $(pwd)"
echo "=============================="

# Check if critical files exist
if [ ! -f "blood_donation/asgi.py" ]; then
    echo "❌ ERROR: blood_donation/asgi.py not found!"
    exit 1
fi

echo "✅ ASGI configuration found"

# Run database migrations before starting server
echo "🔄 Running database migrations..."
python manage.py migrate --noinput
if [ $? -eq 0 ]; then
    echo "✅ Migrations applied successfully"
else
    echo "❌ ERROR: Migrations failed!"
    exit 1
fi

# Try to start Daphne with full error output
echo "🚀 Starting Daphne server..."
exec daphne -b 0.0.0.0 -p $PORT blood_donation.asgi:application 2>&1
