# Database Migration Error Fix

## Problem
```
django.db.utils.ProgrammingError: column accounts_hospital.verified_by_id does not exist
```

## Root Cause
The `verified_by` field was added to the Hospital model in migration `0016_add_hospital_complete_fields.py`, but this migration has **NOT been applied** to your PostgreSQL database on Render.

When Django tries to delete a User or Hospital object, it attempts to set `verified_by_id = NULL` (due to `on_delete=models.SET_NULL`), but the column doesn't exist in the database.

## Solution

### Step 1: Apply Migrations on Render (REQUIRED)

You **MUST** run migrations on your Render deployment. Choose one of these methods:

#### Method A: Via Render Dashboard (Recommended)
1. Go to your Render Dashboard: https://dashboard.render.com
2. Select your web service
3. Go to **Shell** tab
4. Run the following commands:
```bash
python manage.py migrate
```

#### Method B: Add to Render Build Command
Update your `render.yaml` or Render dashboard build command:
```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```

#### Method C: Via Render CLI
```bash
render exec "python manage.py migrate" --service your-service-name
```

### Step 2: Verify Migration Status

After running migrations, verify they were applied:
```bash
python manage.py showmigrations accounts
```

You should see all migrations checked (✓), including:
- [✓] 0012_add_hospital_models
- [✓] 0013_add_hospital_emergency_contact
- [✓] 0014_add_loginotp_model
- [✓] 0015_fix_cascade_delete
- [✓] 0016_add_hospital_complete_fields

### Step 3: Test the Fix

1. Go to Django Admin panel
2. Try deleting a User or Hospital
3. The error should be resolved

## Temporary Fix Applied

I've updated `accounts/admin.py` to handle this error gracefully:
- Catches `ProgrammingError` exceptions
- Shows a clear error message: "Database migration required. Please run: python manage.py migrate"
- Prevents the app from crashing

**However, this is only a temporary fix. You MUST run migrations to fully resolve the issue.**

## Prevention

To prevent this in the future:

1. **Always run migrations after deploying code changes:**
   ```bash
   python manage.py migrate
   ```

2. **Add migration check to your deployment pipeline:**
   ```bash
   python manage.py makemigrations --check
   python manage.py migrate
   ```

3. **Update your `render.yaml` to include migrations:**
   ```yaml
   buildCommand: |
     pip install -r requirements.txt
     python manage.py migrate
     python manage.py collectstatic --noinput
   ```

## Migration Files Reference

The following migrations need to be applied:
- `0012_add_hospital_models.py` - Creates Hospital and HospitalStaff models
- `0013_add_hospital_emergency_contact.py` - Adds emergency_contact field
- `0014_add_loginotp_model.py` - Creates LoginOTP model
- `0015_fix_cascade_delete.py` - Fixes cascade delete issues
- `0016_add_hospital_complete_fields.py` - **Adds verified_by field** (THIS IS THE MISSING ONE)

## Quick Commands Summary

```bash
# Check migration status
python manage.py showmigrations

# Apply migrations
python manage.py migrate

# Check for pending migrations
python manage.py makemigrations --check

# Create new migrations (if needed)
python manage.py makemigrations
```

## Need Help?

If migrations fail, check:
1. Database connection in Render environment variables
2. PostgreSQL service is running
3. Requirements are installed: `pip install -r requirements.txt`
4. Check Render logs for detailed error messages
