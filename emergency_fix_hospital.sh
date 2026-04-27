#!/bin/bash
# Emergency fix for missing accounts_hospital columns
# Run this in Render Shell or SSH to immediately fix the database

echo "========================================"
echo "Emergency Database Fix - Hospital Model"
echo "========================================"
echo ""

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo "ERROR: Run this script from the blood-donation-help directory"
    exit 1
fi

echo "Step 1: Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

echo "Step 2: Checking current migration state..."
python manage.py showmigrations accounts | tail -5
echo ""

echo "Step 3: Running migration..."
python manage.py migrate accounts
echo ""

echo "Step 4: Verifying migration..."
python manage.py showmigrations accounts | grep 0016
echo ""

echo "========================================"
echo "✓ Migration Complete!"
echo "========================================"
echo ""
echo "You can now:"
echo "  - Delete users from Django admin"
echo "  - Access hospital partners page"
echo "  - Access all admin pages"
echo ""
echo "Test it at: https://bloodis-life.online/admin/"
