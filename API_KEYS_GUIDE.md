# API Keys Configuration Guide

This document explains all the API keys used in the Blood Donation Platform and how to configure them.

## 🔑 Required API Keys

### 1. Brevo Email API Key (REQUIRED for production)

**Purpose**: Send emails (notifications, password resets, verifications)

**Current Status**: ⚠️ Placeholder configured - needs real key for production

**How to Get**:
1. Go to https://www.brevo.com/
2. Create a free account
3. Navigate to: Settings → SMTP & API → API Keys
4. Create a new API key (starts with `xkeysib-`)
5. Copy the key

**Configuration**:
```env
BREVO_API_KEY=xkeysib-your-actual-api-key-here
```

**Important**: 
- Must start with `xkeysib-`
- Keep this key secret - never commit to Git
- Add verified sender email in Brevo dashboard

---

### 2. Google Maps API Key (COMPLETELY OPTIONAL)

**Status**: ✅ **NOT REQUIRED** - Using FREE OpenStreetMap + Leaflet!

**What We Use**: 
- 🗺️ **OpenStreetMap** - Free, open-source world maps
- 🍃 **Leaflet.js** - Free, lightweight mapping library
- ✅ **NO API KEY NEEDED** - Works out of the box!

**Benefits**:
- ✅ 100% FREE forever
- ✅ No usage limits
- ✅ No credit card required
- ✅ No API key configuration
- ✅ Privacy-friendly (no Google tracking)
- ✅ Works immediately after deployment

**Features Available**:
- 🗺️ Interactive maps
- 📍 Location markers
- 🌐 Geolocation support
- 📏 Distance calculations
- 🔍 Search functionality

**If You Still Want Google Maps** (Optional):
1. Go to https://console.cloud.google.com/google/maps-apis
2. Create a project and enable Maps JavaScript API
3. Create an API key
4. Add to `.env`:
   ```env
   GOOGLE_MAPS_API_KEY=AIzaSy-your-key-here
   ```

**Pricing**: 
- OpenStreetMap: **FREE FOREVER**
- Google Maps (optional): $200/month free credit, then pay-as-you-go

---

## 🔐 Already Configured (Don't Change)

### 3. Django Secret Key

**Purpose**: Cryptographic signing, session security, password reset tokens

**Current Status**: ✅ Configured

**Location**: `.env` file
```env
SECRET_KEY=&$NUr51ulcQ-yIgapD0dY8X4EZ2ho7fq_RTVF9vHBOsCLG3J6nA%kb!etmKSjx#z
```

**Important**: 
- Already generated and working
- NEVER share or commit this key
- For production, generate a new one using:
  ```python
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

---

## 📊 Database Configuration

### MySQL/PostgreSQL Database (Optional for production)

**Current Status**: ⚠️ Using SQLite for development

**For Production** (Render/Heroku):
```env
DB_NAME=blood_donation_db
DB_USER=your-db-username
DB_PASSWORD=your-db-password
DB_HOST=your-db-host
DB_PORT=5432  # PostgreSQL or 3306 for MySQL
```

**Development**: Using SQLite (db.sqlite3) - no configuration needed

---

## 🚀 How to Configure

### For Development (Local)

1. Open `.env` file in project root
2. Replace placeholder values with actual keys:
   ```env
   BREVO_API_KEY=xkeysib-your-real-key-here
   GOOGLE_MAPS_API_KEY=AIzaSy-your-real-key-here
   ```
3. Save the file
4. Restart Django server:
   ```bash
   python manage.py runserver
   ```

### For Production (Render)

1. Go to your Render dashboard
2. Select your web service
3. Go to "Environment" tab
4. Add environment variables:
   - `BREVO_API_KEY` = `xkeysib-your-real-key`
   - `GOOGLE_MAPS_API_KEY` = `AIzaSy-your-real-key`
   - `SECRET_KEY` = (generate new production key)
5. Save and redeploy

---

## ✅ Verification

After adding API keys, restart your server and check the logs:

**Expected Output**:
```
✅ Brevo HTTP API configured - using HTTPS for reliable email delivery (key length: 72)
✅ Google Maps API configured (key length: 39)
```

**If you see errors**:
```
❌ BREVO_API_KEY not configured! Email sending will FAIL.
ℹ️ Google Maps API key not configured - location features will use fallback
```

---

## 🔒 Security Best Practices

1. **Never commit `.env` to Git** - Already in `.gitignore`
2. **Use different keys for dev/production**
3. **Rotate keys regularly** (every 3-6 months)
4. **Restrict API keys** to your domain/IP
5. **Monitor usage** in respective dashboards
6. **Use environment variables** in production, not hardcoded values

---

## 📝 API Key Summary

| API Key | Status | Required | Purpose |
|---------|--------|----------|---------|  
| `SECRET_KEY` | ✅ Configured | **YES** | Django security |
| `BREVO_API_KEY` | ⚠️ Placeholder | Production | Email sending |
| `GOOGLE_MAPS_API_KEY` | ✅ **NOT NEEDED** | **NO** | Using FREE OpenStreetMap |
| `DB_PASSWORD` | ⚠️ Placeholder | Production | Database access |

---

## 🆘 Troubleshooting

### Email Not Sending
- Check BREVO_API_KEY starts with `xkeysib-`
- Verify sender email in Brevo dashboard
- Check Brevo account limits (free tier: 300 emails/day)

### Google Maps Not Working
- **You don't need Google Maps!** We use FREE OpenStreetMap by default
- Maps work out of the box with Leaflet.js + OpenStreetMap
- If you specifically want Google Maps:
  - Verify API key is correct (starts with `AIzaSy`)
  - Check APIs are enabled in Google Cloud Console
  - Verify billing is enabled (free tier available)
  - Check browser console for specific error messages

### Server Won't Start
- Check `.env` file syntax (no extra spaces)
- Ensure all required variables are present
- Check logs for specific error messages

---

## 📚 Resources

- **Brevo Documentation**: https://developers.brevo.com/
- **Google Maps Documentation**: https://developers.google.com/maps/documentation/javascript
- **Django Environment Variables**: https://docs.djangoproject.com/en/4.2/topics/settings/
- **Render Environment Variables**: https://render.com/docs/environment-variables

---

**Last Updated**: April 16, 2026
