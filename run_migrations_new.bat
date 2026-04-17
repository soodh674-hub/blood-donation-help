@echo off
echo ========================================
echo Running Database Migrations
echo ========================================
echo.

echo Step 1: Checking for new migrations...
python manage.py makemigrations
echo.

echo Step 2: Applying migrations...
python manage.py migrate
echo.

echo ========================================
echo Migrations Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Review the migration files created
echo 2. Commit them to Git: git add .
echo 3. Commit: git commit -m "Add database indexes for donor search optimization"
echo 4. Push: git push
echo.
pause
