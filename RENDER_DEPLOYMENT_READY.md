# 🚀 Render Deployment Guide - BloodLife

## ✅ Pre-Deployment Checklist

### 1. Install Python (If Not Already Installed)
```powershell
# Download from: https://www.python.org/downloads/
# IMPORTANT: Check "Add Python to PATH" during installation
```

### 2. Run Pre-Deployment Setup
```powershell
cd "c:\Users\mypc0\OneDrive\Desktop\New folder\blood-donation-help"
.\PRE_DEPLOYMENT_SETUP.ps1
```

This script will:
- ✅ Install all dependencies
- ✅ Create necessary directories
- ✅ Check environment variables
- ✅ Run all migrations
- ✅ Collect static files
- ✅ Start local server for testing

### 3. Test Locally
After running the setup script, test these features:

**Core Features:**
- [ ] Homepage loads correctly (http://127.0.0.1:8000)
- [ ] User registration works
- [ ] User login works
- [ ] Donor search works
- [ ] Blood request creation works
- [ ] Notifications display
- [ ] Admin panel accessible (http://127.0.0.1:8000/secure-admin-panel-x92/)

**Check for Errors:**
- [ ] No 500 errors in browser
- [ ] No migration errors in terminal
- [ ] All static files load (CSS, JS, images)
- [ ] No missing template errors

### 4. Fix Any Local Errors
If you find errors:
1. Note the error message
2. Fix the issue in the code
3. Run migrations again if needed: `python manage.py migrate`
4. Test again

### 5. Prepare for Git
```powershell
# Navigate to project
cd "c:\Users\mypc0\OneDrive\Desktop\New folder\blood-donation-help"

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Ready for Render deployment - all migrations complete"

# Add remote (replace with your GitHub repo URL)
git remote add origin https://github.com/YOUR_USERNAME/blood-donation-help.git

# Push to GitHub
git push -u origin main
```

---

## 🌐 Deploy to Render

### Step 1: Create Web Service
1. Go to https://render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select your repository

### Step 2: Configure Service
```
Name: bloodlife
Region: Oregon (or closest to your users)
Branch: main
Root Directory: blood-donation-help
Runtime: Python 3
Build Command: bash render_build.sh
Start Command: daphne -b 0.0.0.0 -p $PORT blood_donation.asgi:application
```

### Step 3: Set Environment Variables

**Required Variables:**
```
SECRET_KEY = <generate a strong random key>
DEBUG = False
ALLOWED_HOSTS = bloodis-life.online,.onrender.com,localhost,127.0.0.1
```

**Database (Choose ONE):**

**Option A: Render PostgreSQL (Recommended)**
```
DATABASE_URL = <from Render PostgreSQL dashboard>
```

**Option B: Supabase PostgreSQL**
```
SUPABASE_HOST = db.xxxxx.supabase.co
SUPABASE_PORT = 5432
SUPABASE_DBNAME = postgres
SUPABASE_USER = postgres
SUPABASE_PASSWORD = <your supabase password>
SUPABASE_PROJECT_REF = <your project ref>
```

**Optional Variables:**
```
GOOGLE_MAPS_API_KEY = <your Google Maps API key>
EMAIL_HOST_USER = your-email@gmail.com
EMAIL_HOST_PASSWORD = <your app password>
EMAIL_USE_TLS = True
CREATE_SUPERUSER = true
SUPERUSER_USERNAME = admin
SUPERUSER_EMAIL = admin@example.com
```

### Step 4: Deploy
1. Click **"Create Web Service"**
2. Wait for build and deployment (5-10 minutes)
3. Check the logs for any errors
4. Visit your live site!

---

## 🔧 Troubleshooting

### Migration Errors on Render
If migrations fail on Render:
1. Check the build logs
2. The Procfile has a release command that runs migrations automatically
3. If it still fails, SSH into Render shell and run:
   ```bash
   python manage.py migrate --noinput
   ```

### Static Files Not Loading
- WhiteNoise is configured to serve static files
- Make sure `collectstatic` runs successfully in build logs
- Check that `WHITENOISE_USE_FINDERS = True` in settings

### Database Connection Errors
- Verify your DATABASE_URL or SUPABASE_* variables
- Check that SSL is enabled (required for Supabase)
- Test connection locally first

### 500 Internal Server Error
- Check Render logs for the actual error
- Common causes:
  - Missing environment variables
  - Database not migrated
  - Missing dependencies
  - Python version mismatch

---

## 📋 Post-Deployment Checklist

After deploying to Render:

- [ ] Site loads without errors
- [ ] User registration works
- [ ] User login works
- [ ] Database is connected
- [ ] Static files load (CSS, JS)
- [ ] Email notifications work (if configured)
- [ ] Admin panel accessible
- [ ] WebSocket connections work (for real-time features)
- [ ] No console errors in browser

---

## 🎯 Quick Commands Reference

**Local Development:**
```powershell
# Setup everything
.\PRE_DEPLOYMENT_SETUP.ps1

# Run migrations only
python manage.py makemigrations
python manage.py migrate

# Start server
python manage.py runserver

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

**On Render (via Shell):**
```bash
# Run migrations
python manage.py migrate

# Check Django setup
python manage.py check

# Create superuser
python manage.py createsuperuser

# View logs
# Available in Render dashboard
```

---

## 📊 Your Deployment Files

All deployment files are ready:

✅ `Procfile` - Tells Render how to run your app
✅ `render_build.sh` - Build script for Render
✅ `requirements.txt` - Python dependencies
✅ `runtime.txt` - Python version
✅ `.env.example` - Environment variable template
✅ `PRE_DEPLOYMENT_SETUP.ps1` - Local setup script

---

## 🆘 Need Help?

If you encounter issues:
1. Check the Render build logs
2. Check the Render runtime logs
3. Test locally first with `.\PRE_DEPLOYMENT_SETUP.ps1`
4. Review this guide step by step

**Common Issues & Solutions:**
- Python not found → Install Python and add to PATH
- Migration errors → Run `python manage.py migrate`
- Missing SECRET_KEY → Add to environment variables
- Database errors → Check DATABASE_URL format
- Static files missing → Run `collectstatic`

---

**Your BloodLife app is production-ready! 🎉**

Just follow these steps and you'll have a smooth deployment!
