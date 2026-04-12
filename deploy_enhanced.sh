#!/bin/bash
# Enhanced deployment script with comprehensive error checking
# Usage: bash deploy_enhanced.sh

set -e  # Exit on any error

echo "======================================"
echo "  BloodLife Platform - Enhanced Deploy"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Error handler
error_handler() {
    echo -e "${RED}❌ Error occurred in deployment at line $1${NC}"
    echo "Please check the error message above and fix it before retrying"
    exit 1
}

trap 'error_handler $LINENO' ERR

# Step 1: Environment validation
echo -e "${YELLOW}Step 1: Validating environment...${NC}"
if [ -z "$DATABASE_URL" ] && [ -z "$SUPABASE_HOST" ]; then
    echo -e "${RED}❌ Database configuration not found!${NC}"
    echo "Please set DATABASE_URL or SUPABASE_* environment variables"
    exit 1
fi
echo -e "${GREEN}✅ Environment validated${NC}"
echo ""

# Step 2: Install dependencies
echo -e "${YELLOW}Step 2: Installing dependencies...${NC}"
pip install -r requirements.txt --quiet
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 3: Emergency database fix
echo -e "${YELLOW}Step 3: Running emergency database fixes...${NC}"
if python emergency_db_fix.py; then
    echo -e "${GREEN}✅ Emergency fixes applied${NC}"
else
    echo -e "${YELLOW}⚠️  Emergency fix had issues (may already be fixed)${NC}"
fi
echo ""

# Step 4: Django checks
echo -e "${YELLOW}Step 4: Running Django system checks...${NC}"
python manage.py check --deploy
echo -e "${GREEN}✅ Django checks passed${NC}"
echo ""

# Step 5: Database migrations
echo -e "${YELLOW}Step 5: Applying database migrations...${NC}"
python manage.py makemigrations --noinput || echo -e "${YELLOW}⚠️  No new migrations${NC}"
python manage.py migrate --noinput
echo -e "${GREEN}✅ Migrations applied${NC}"
echo ""

# Step 6: Collect static files
echo -e "${YELLOW}Step 6: Collecting static files...${NC}"
python manage.py collectstatic --noinput --clear
echo -e "${GREEN}✅ Static files collected${NC}"
echo ""

# Step 7: Create superuser if needed
echo -e "${YELLOW}Step 7: Checking admin user...${NC}"
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Creating admin user...')
    User.objects.create_superuser('admin', 'admin@bloodis-life.online', 'admin123')
    print('✅ Admin user created')
else:
    print('✅ Superuser already exists')
"
echo ""

# Step 8: Verify deployment
echo -e "${YELLOW}Step 8: Running deployment verification...${NC}"
python manage.py shell -c "
import sys
print('Running deployment checks...')

# Check database connection
from django.db import connection
try:
    connection.ensure_connection()
    print('✅ Database connection: OK')
except Exception as e:
    print(f'❌ Database connection: FAILED - {e}')
    sys.exit(1)

# Check static files
from django.conf import settings
import os
if os.path.exists(settings.STATIC_ROOT):
    static_count = len(os.listdir(settings.STATIC_ROOT))
    print(f'✅ Static files: {static_count} files collected')
else:
    print('⚠️  Static files directory not found')

# Check email configuration
email_backend = getattr(settings, 'EMAIL_BACKEND', 'Not set')
print(f'✅ Email backend: {email_backend.split(\".\")[-1]}')

print('\\n✅ All deployment checks passed!')
"
echo ""

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  ✅ DEPLOYMENT COMPLETED SUCCESSFULLY${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Your application is ready to start!"
echo "Run: bash start_server.sh"
echo ""
