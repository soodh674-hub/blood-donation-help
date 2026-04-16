# 🐍 Python Installation Guide for BloodLife

## ⚠️ Python Not Found!

Python is not installed on your system or not added to PATH. You need to install Python before you can run the Django application locally.

---

## 📥 Step 1: Install Python

### Option A: Install from Python.org (Recommended)

1. **Download Python:**
   - Go to: https://www.python.org/downloads/
   - Click the yellow button "Download Python 3.x.x" (latest version)
   - OR go to: https://www.python.org/downloads/windows/

2. **Run the Installer:**
   - Double-click the downloaded file
   - ⚠️ **IMPORTANT:** Check the box **"Add Python to PATH"** at the bottom!
   - Click **"Install Now"**
   - Wait for installation to complete
   - Click **"Close"**

3. **Verify Installation:**
   - Open a NEW PowerShell window (important: must be NEW!)
   - Run: `python --version`
   - You should see: `Python 3.x.x`

### Option B: Install from Microsoft Store

1. Open Microsoft Store
2. Search for "Python 3.12" (or latest version)
3. Click "Get" or "Install"
4. Wait for installation

**Note:** Microsoft Store version sometimes has PATH issues. Option A is recommended.

---

## ✅ Step 2: Verify Python is Working

Open a **NEW** PowerShell window and run:

```powershell
python --version
```

You should see something like: `Python 3.12.0`

Also test pip (Python package manager):

```powershell
pip --version
```

You should see: `pip 23.x.x from ...`

---

## 🚀 Step 3: Run BloodLife Setup

Once Python is installed and working:

```powershell
# Navigate to your project
cd "c:\Users\mypc0\OneDrive\Desktop\New folder\blood-donation-help"

# Run the automated setup script
.\PRE_DEPLOYMENT_SETUP.ps1
```

This will:
- ✅ Install all dependencies
- ✅ Run database migrations
- ✅ Collect static files
- ✅ Start the development server

---

## 🧪 Step 4: Test Locally

After the setup script starts the server, open your browser and test:

### Core Pages:
1. **Homepage:** http://127.0.0.1:8000
2. **Registration:** http://127.0.0.1:8000/accounts/register/
3. **Login:** http://127.0.0.1:8000/accounts/login/
4. **Donor Search:** http://127.0.0.1:8000/search/donors/
5. **Admin Panel:** http://127.0.0.1:8000/secure-admin-panel-x92/

### Test Checklist:
- [ ] Homepage loads without errors
- [ ] Can see the hero section and features
- [ ] CSS styles are applied (not broken)
- [ ] Navigation menu works
- [ ] Can register a new user
- [ ] Can login with registered user
- [ ] Can search for donors
- [ ] Can create a blood request (if logged in)
- [ ] Admin panel is accessible
- [ ] No errors in PowerShell terminal
- [ ] No errors in browser console (F12 → Console tab)

---

## 🐛 Troubleshooting

### ❌ "python is not recognized"

**Problem:** Python not in PATH

**Solutions:**

1. **Reinstall Python:**
   - Download from https://www.python.org/downloads/
   - During installation, CHECK "Add Python to PATH"
   - Complete installation
   - Open a NEW PowerShell window

2. **Manually Add to PATH:**
   - Press `Win + R`, type `sysdm.cpl`, press Enter
   - Click "Advanced" tab → "Environment Variables"
   - Under "System variables", find "Path" → Click "Edit"
   - Click "New" and add these paths:
     ```
     C:\Users\mypc0\AppData\Local\Programs\Python\Python312\
     C:\Users\mypc0\AppData\Local\Programs\Python\Python312\Scripts\
     ```
     (Adjust Python312 to your version)
   - Click OK on all windows
   - Open a NEW PowerShell window
   - Test: `python --version`

3. **Use Full Path (Temporary):**
   ```powershell
   "C:\Users\mypc0\AppData\Local\Programs\Python\Python312\python.exe" --version
   ```

### ❌ "pip is not recognized"

**Solution:** Same as above - Python and pip are installed together

### ❌ Permission Errors

**Solution:** Run PowerShell as Administrator:
- Right-click PowerShell → "Run as Administrator"

### ❌ Dependencies Fail to Install

**Solution:**
```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Then install dependencies
pip install -r requirements.txt
```

### ❌ Migration Errors

**Solution:**
```powershell
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

---

## 📋 Manual Setup (If Script Doesn't Work)

If the PowerShell script has issues, run these commands manually:

```powershell
# Navigate to project
cd "c:\Users\mypc0\OneDrive\Desktop\New folder\blood-donation-help"

# Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Create directories
New-Item -ItemType Directory -Path "logs" -Force
New-Item -ItemType Directory -Path "media" -Force
New-Item -ItemType Directory -Path "media/medical_certificates" -Force
New-Item -ItemType Directory -Path "media/profile_photos" -Force

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser (optional)
python manage.py createsuperuser

# Start server
python manage.py runserver
```

---

## 🎯 Quick Start Summary

1. **Install Python** from https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH"
   
2. **Open NEW PowerShell** and verify:
   ```powershell
   python --version
   ```

3. **Run setup:**
   ```powershell
   cd "c:\Users\mypc0\OneDrive\Desktop\New folder\blood-donation-help"
   .\PRE_DEPLOYMENT_SETUP.ps1
   ```

4. **Test at:** http://127.0.0.1:8000

5. **Fix any errors** before deploying to Render

---

## 📞 Need Help?

If you're stuck:
1. Check the error message carefully
2. Make sure Python is installed correctly
3. Make sure you're using a NEW PowerShell window after installing Python
4. Try the manual setup commands above

**Common mistake:** Not checking "Add Python to PATH" during installation!

---

## ✅ After Python is Installed

Once Python is working, I can help you:
- Run all migrations
- Start the development server
- Test all features
- Fix any errors
- Prepare for Render deployment

Just let me know when Python is installed! 🚀
