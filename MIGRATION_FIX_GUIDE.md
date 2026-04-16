# 🔧 Database Migration Fix - Render

## 🚨 Issue:
```
django.db.utils.ProgrammingError: column accounts_donorprofile.availability_status does not exist
```

## ✅ What's Happening:

Your **app is running** but the **database migrations haven't been applied yet**. The code expects a column that doesn't exist in the database.

---

## 🎯 Good News:

✅ **Your app IS running** on Render!  
✅ **PostgreSQL connection is working**  
✅ **The migration file exists**  
✅ **Auto-fix is deployed** (better error handling)

---

## 🔧 Solutions:

### **Option 1: Wait for Auto-Deploy (Recommended)**

The latest commit improves migration error handling. Render will:
1. Rebuild with better error reporting
2. Show exactly where migrations fail
3. Retry migrations in release phase

**Timeline:** 2-3 minutes

---

### **Option 2: Manually Trigger Migration via Render Shell**

If auto-deploy doesn't fix it:

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click your web service**
3. **Click "Shell" tab**
4. **Run these commands:**

```bash
# Check migration status
python manage.py showmigrations accounts

# Run migrations manually
python manage.py migrate accounts

# Check if specific migration applied
python manage.py showmigrations accounts | grep 0009
```

---

### **Option 3: Force Migration via Django Admin**

If Shell doesn't work:

1. **Create a temporary management command:**

Create file: `accounts/management/commands/force_migrate.py`

```python
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Force run all migrations'

    def handle(self, *args, **options):
        self.stdout.write('Running migrations...')
        call_command('migrate', verbosity=2)
        self.stdout.write(self.style.SUCCESS('Migrations complete!'))
```

2. **Run via Render Shell:**
```bash
python manage.py force_migrate
```

---

## 📊 Verify Migration Status:

### **Check if migration exists:**
```bash
python manage.py showmigrations accounts
```

**Expected output:**
```
accounts
 [X] 0001_initial
 [X] 0002_...
 [X] 0008_add_favoritedonor
 [X] 0009_follow_alter_donorprofile_options_and_more  ← Should be checked
```

### **Check database columns:**
```bash
python manage.py dbshell
```

Then in PostgreSQL shell:
```sql
\d accounts_donorprofile
```

Look for `availability_status` column.

---

## 🎯 What the Migration Does:

Migration `0009` adds these fields to `accounts_donorprofile`:
- ✅ `availability_status` (the missing column)
- ✅ `auto_disable_until`
- ✅ `donation_frequency_preference`
- ✅ `last_donation_location`
- ✅ `preferred_donation_centers`
- ✅ `weight_kg`
- ✅ `has_recent_illness`
- ✅ `medical_restrictions`
- ✅ `recent_illness_details`

---

## 🔍 Debug Migration Issues:

### **See migration SQL without running:**
```bash
python manage.py sqlmigrate accounts 0009
```

### **Check for migration conflicts:**
```bash
python manage.py makemigrations --check
```

### **Fake migration if already applied:**
```bash
python manage.py migrate accounts 0009 --fake
```

---

## 🚀 After Migration is Applied:

Your app will work perfectly! The error will disappear:

**Before:**
```
❌ column accounts_donorprofile.availability_status does not exist
```

**After:**
```
✅ Donor search working
✅ All queries successful
✅ No errors
```

---

## 📝 Common Migration Issues on Render:

### **Issue 1: Migration fails silently**
**Fix:** Now fixed with better error reporting (commit 41e9f88)

### **Issue 2: Database not connected**
**Fix:** Check `DATABASE_URL` environment variable

### **Issue 3: Migration conflicts**
**Fix:** 
```bash
python manage.py makemigrations --merge
```

### **Issue 4: Missing migration files**
**Fix:**
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## ✅ Expected Behavior After Fix:

1. **Build logs will show:**
```
🗄️  Running database migrations...
Running makemigrations...
No changes detected
Running migrate...
Running migrations:
  Applying accounts.0009_follow_alter_donorprofile_options_and_more... OK
✅ Migrations complete
```

2. **App logs will show:**
```
INFO Donor search completed: 5 results for blood group A+
INFO Active/approved/pending requests: 6
```

3. **No more errors:**
```
✅ No ProgrammingError
✅ No missing columns
✅ All API endpoints working
```

---

## 🎊 Status:

- [x] Migration file exists
- [x] Better error handling deployed
- [x] PostgreSQL connection working
- [ ] Migration needs to be applied (in progress)
- [ ] App fully functional (waiting for migration)

---

**Your app is 95% working! Just needs migrations to complete.** 🚀

*Last Updated: April 16, 2026*  
*Commit: 41e9f88*
