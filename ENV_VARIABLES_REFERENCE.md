# 🔑 Environment Variables Quick Reference

Copy and paste these into your Render Dashboard → Environment tab

---

## ✅ Required Variables

### Database
```
Key:   DATABASE_URL
Value: postgresql://user:password@host:5432/dbname
Note:  Auto-filled if using render.yaml with PostgreSQL
```

### Django Security
```
Key:   SECRET_KEY
Value: <auto-generate or use long random string>
Note:  Render can auto-generate this

Key:   DEBUG
Value: False
Note:  NEVER set to True in production!

Key:   DJANGO_SETTINGS_MODULE
Value: blood_donation.settings
```

### Allowed Hosts
```
Key:   ALLOWED_HOSTS
Value: *.onrender.com,localhost,127.0.0.1
Note:  Add your custom domain if you have one

Key:   CSRF_TRUSTED_ORIGINS
Value: https://*.onrender.com
Note:  Add https://yourdomain.com if using custom domain
```

### Email (Brevo)
```
Key:   BREVO_API_KEY
Value: xkeysib-your-actual-api-key-here
Note:  Get from https://app.brevo.com/
       Key MUST start with "xkeysib-"

Key:   DEFAULT_FROM_EMAIL
Value: noreply@yourdomain.com
Note:  Must be verified in Brevo

Key:   DEFAULT_FROM_EMAIL_NAME
Value: BloodLife Platform

Key:   EMAIL_BACKEND
Value: blood_donation.email_backend.BrevoAPIEmailBackend
```

---

## ⚙️ Optional Variables

### Google Maps (Optional)
```
Key:   GOOGLE_MAPS_API_KEY
Value: AIza-your-google-maps-key
Note:  App works without this (uses free OpenStreetMap)
       Get from: https://console.cloud.google.com
```

### Admin User Auto-Creation
```
Key:   CREATE_SUPERUSER
Value: true

Key:   SUPERUSER_USERNAME
Value: admin

Key:   SUPERUSER_EMAIL
Value: admin@yourdomain.com

Key:   SUPERUSER_PASSWORD
Value: your-secure-password
Note:  Set to "false" after first deployment for security
```

### Celery (Background Tasks)
```
Key:   CELERY_TASK_ALWAYS_EAGER
Value: True
Note:  Set to True for free tier (no Redis needed)
       Tasks run synchronously instead of async
```

### Redis (Optional - for WebSockets)
```
Key:   REDIS_URL
Value: redis://your-redis-url:6379/0
Note:  Only needed if you want real-time WebSocket features
       Not required for basic functionality
```

---

## 📋 Complete Copy-Paste List

Here's everything you need in one list:

```
DJANGO_SETTINGS_MODULE=blood_donation.settings
DEBUG=False
ALLOWED_HOSTS=*.onrender.com,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://*.onrender.com
EMAIL_BACKEND=blood_donation.email_backend.BrevoAPIEmailBackend
DEFAULT_FROM_EMAIL_NAME=BloodLife Platform
CELERY_TASK_ALWAYS_EAGER=True
```

Plus these (fill in your values):
```
DATABASE_URL=postgresql://...  (from Render PostgreSQL)
SECRET_KEY=...  (auto-generate or random string)
BREVO_API_KEY=xkeysib-...  (from Brevo)
DEFAULT_FROM_EMAIL=...  (your verified email)
```

---

## 🔐 How to Generate Secure Values

### Generate SECRET_KEY
```python
# Run this in Python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Get BREVO_API_KEY
1. Go to https://app.brevo.com/
2. Sign up / Log in
3. Go to Profile → SMTP & API → API Keys
4. Create new API key
5. Copy the key (starts with `xkeysib-`)

### Get DATABASE_URL
1. Create PostgreSQL database in Render
2. Go to database dashboard
3. Copy "Internal Database URL"
4. Paste as value

---

## 🚫 What NOT to Do

❌ **Don't** set `DEBUG=True` in production
❌ **Don't** use default/example values
❌ **Don't** commit `.env` file to Git
❌ **Don't** share your SECRET_KEY
❌ **Don't** use weak passwords for superuser
❌ **Don't** leave `CREATE_SUPERUSER=true` permanently

---

## ✅ Verification Checklist

After setting environment variables:

- [ ] `DATABASE_URL` is set and correct
- [ ] `SECRET_KEY` is a long random string
- [ ] `DEBUG` is set to `False` (not True)
- [ ] `ALLOWED_HOSTS` includes your domain
- [ ] `BREVO_API_KEY` starts with `xkeysib-`
- [ ] `DEFAULT_FROM_EMAIL` is verified in Brevo
- [ ] `DJANGO_SETTINGS_MODULE` is `blood_donation.settings`
- [ ] `CELERY_TASK_ALWAYS_EAGER` is `True` (for free tier)

---

## 🔄 Updating Variables

To change environment variables after deployment:

1. Go to Render Dashboard
2. Select your web service
3. Click "Environment" tab
4. Edit the variable value
5. Click "Save Changes"
6. Service will automatically redeploy

---

## 📊 Variable Priority

Settings are loaded in this order (last wins):

1. `settings.py` defaults
2. `.env` file (local development only)
3. Render environment variables
4. OS environment variables

**Render variables override everything** ✅

---

**Keep this reference handy for quick setup! 📌**
