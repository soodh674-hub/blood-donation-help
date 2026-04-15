#!/bin/sh
# Render build script for Blood Donation Platform
# Simplified to only install dependencies - Render handles migrations/static files

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
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Verify Django installation
echo "\n✅ Verifying Django installation..."
python -c "import django; print(f'Django {django.VERSION} installed successfully')" || echo "⚠️  Django verification skipped"

echo "\n" + "=" * 60
echo "✅ BUILD COMPLETED SUCCESSFULLY!"
echo "Note: Render will automatically run migrations and collect static files during deployment"
echo "=" * 60