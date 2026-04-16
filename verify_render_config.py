#!/usr/bin/env python
"""
Pre-deployment verification script for Render.
Run this locally before pushing to Render to catch common issues.
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} NOT FOUND")
        return False

def check_file_content(filepath, required_content, description):
    """Check if file contains required content."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if required_content in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description} - Content not found")
                return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def main():
    print("=" * 70)
    print("🔍 BLOODLIFE PLATFORM - RENDER DEPLOYMENT VERIFICATION")
    print("=" * 70)
    print()
    
    # Get the project root (blood-donation-help directory)
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    
    all_checks_passed = True
    
    # 1. Check essential files
    print("📁 Checking Essential Files...")
    print("-" * 70)
    files_to_check = [
        ("manage.py", "Django manage.py"),
        ("requirements.txt", "Requirements file"),
        ("Procfile", "Render Procfile"),
        ("render_build.sh", "Render build script"),
        ("render.yaml", "Render configuration"),
        (".renderignore", "Render ignore file"),
        ("blood_donation/settings.py", "Django settings"),
        ("blood_donation/wsgi.py", "WSGI configuration"),
        ("blood_donation/asgi.py", "ASGI configuration"),
    ]
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    
    print()
    
    # 2. Check file contents
    print("📝 Checking File Contents...")
    print("-" * 70)
    
    # Check Procfile uses gunicorn
    all_checks_passed &= check_file_content(
        "Procfile",
        "gunicorn",
        "Procfile uses Gunicorn (not Daphne)"
    )
    
    # Check render_build.sh has correct settings module
    all_checks_passed &= check_file_content(
        "render_build.sh",
        "DJANGO_SETTINGS_MODULE=blood_donation.settings",
        "Build script has correct DJANGO_SETTINGS_MODULE"
    )
    
    # Check requirements.txt has gunicorn
    all_checks_passed &= check_file_content(
        "requirements.txt",
        "gunicorn",
        "requirements.txt includes gunicorn"
    )
    
    # Check requirements.txt has psycopg2-binary
    all_checks_passed &= check_file_content(
        "requirements.txt",
        "psycopg2-binary",
        "requirements.txt includes psycopg2-binary"
    )
    
    # Check requirements.txt has whitenoise
    all_checks_passed &= check_file_content(
        "requirements.txt",
        "whitenoise",
        "requirements.txt includes whitenoise"
    )
    
    print()
    
    # 3. Check render.yaml
    print("⚙️  Checking Render Configuration...")
    print("-" * 70)
    
    try:
        with open("render.yaml", 'r') as f:
            content = f.read()
            
            checks = [
                ("type: web", "Web service defined"),
                ("env: python", "Python environment"),
                ("buildCommand", "Build command"),
                ("startCommand", "Start command"),
                ("DATABASE_URL", "DATABASE_URL env var"),
                ("SECRET_KEY", "SECRET_KEY env var"),
                ("gunicorn", "Gunicorn in start command"),
            ]
            
            for check_str, description in checks:
                if check_str in content:
                    print(f"✅ {description}")
                else:
                    print(f"❌ {description}")
                    all_checks_passed = False
    except Exception as e:
        print(f"❌ Error reading render.yaml: {e}")
        all_checks_passed = False
    
    print()
    
    # 4. Check settings.py
    print("🔧 Checking Django Settings...")
    print("-" * 70)
    
    try:
        with open("blood_donation/settings.py", 'r') as f:
            content = f.read()
            
            # Check for IS_RENDER detection
            if "IS_RENDER" in content:
                print("✅ IS_RENDER environment detection present")
            else:
                print("❌ IS_RENDER environment detection missing")
                all_checks_passed = False
            
            # Check for WhiteNoise middleware
            if "whitenoise.middleware.WhiteNoiseMiddleware" in content:
                print("✅ WhiteNoise middleware configured")
            else:
                print("❌ WhiteNoise middleware missing")
                all_checks_passed = False
            
            # Check for PostgreSQL support
            if "dj_database_url" in content:
                print("✅ Database URL parsing configured")
            else:
                print("❌ Database URL parsing missing")
                all_checks_passed = False
                
    except Exception as e:
        print(f"❌ Error reading settings.py: {e}")
        all_checks_passed = False
    
    print()
    
    # 5. Check for common issues
    print("⚠️  Checking for Common Issues...")
    print("-" * 70)
    
    # Check if db.sqlite3 should be in .gitignore
    if os.path.exists("db.sqlite3"):
        print("⚠️  db.sqlite3 exists - Make sure it's in .gitignore")
        print("   (Render uses PostgreSQL, not SQLite)")
    
    # Check if render_build.sh is executable (on Unix-like systems)
    if os.name != 'nt':  # Not Windows
        if os.access("render_build.sh", os.X_OK):
            print("✅ render_build.sh is executable")
        else:
            print("⚠️  render_build.sh is not executable")
            print("   Run: chmod +x render_build.sh")
            all_checks_passed = False
    else:
        print("✅ Skipping executable check (Windows)")
    
    print()
    
    # Final summary
    print("=" * 70)
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED! Your app is ready for Render deployment!")
        print()
        print("📋 Next Steps:")
        print("1. Commit and push to GitHub:")
        print("   git add .")
        print('   git commit -m "Ready for Render deployment"')
        print("   git push origin main")
        print()
        print("2. Deploy on Render:")
        print("   - Go to render.com")
        print("   - New + → Blueprint")
        print("   - Connect your GitHub repo")
        print("   - Fill in environment variables")
        print("   - Click Apply")
    else:
        print("❌ SOME CHECKS FAILED! Please fix the issues above before deploying.")
        print()
        print("📖 See RENDER_DEPLOYMENT_GUIDE.md for detailed instructions")
    print("=" * 70)
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    sys.exit(main())
