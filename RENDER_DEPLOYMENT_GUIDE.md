# 🚀 Render Deployment Guide - BloodLife Platform

Complete guide to deploy your BloodLife Blood Donation Platform on Render.

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Deployment (Recommended)](#quick-deployment-recommended)
- [Manual Deployment](#manual-deployment)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Email Configuration](#email-configuration)
- [Troubleshooting](#troubleshooting)
- [Post-Deployment](#post-deployment)

---

## ✅ Prerequisites

1. **GitHub Account** - Your code should be on GitHub
2. **Render Account** - Sign up at [render.com](https://render.com)
3. **Brevo Account** (for emails) - Sign up at [brevo.com](https://www.brevo.com)
4. **Google Maps API Key** (optional) - Get from [Google Cloud Console](https://console.cloud.google.com)

---

## 🎯 Quick Deployment (Recommended)

### Option 1: One-Click Deploy with render.yaml

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Ready for Render deployment"
   git push origin main
   ```

2. **Connect to Render**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`

3. **Configure Environment Variables**
   - Render will prompt you to configure variables marked as `sync: false`
   - Fill in the required values (see [Environment Variables](#environment-variables))

4. **Deploy**
   - Click "Apply"
   - Wait for build and deployment (~5-10 minutes)

---

## 🔧 Manual Deployment

### Step 1: Create PostgreSQL Database

1. Go to Render Dashboard
2. Click "New +" → "PostgreSQL"
3. Configure:
   - **Name**: `bloodlife-db`
   - **Database**: `bloodlife_db`
   - **User**: `bloodlife_user`
   - **Region**: Choose closest to your users
   - **Plan**: Free (or upgrade for production)
4. Click "Create"
5. **Copy the Internal Database URL** (will look like: `postgresql://user:pass@host:5432/db`)

### Step 2: Create Web Service

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `bloodlife-platform`
   - **Region**: Same as your database
   - **Branch**: `main`
   - **Root Directory**: Leave blank (or `blood-donation-help` if repo root is different)
   - **Runtime**: `Python 3`
   - **Build Command**: `./render_build.sh`
   - **Start Command**: `gunicorn blood_donation.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120`
   - **Plan**: Free

### Step 3: Set Environment Variables

In your Web Service dashboard, go to "Environment" tab and add:

#### Required Variables:
```bash
DJANGO_SETTINGS_MODULE=blood_donation.settings
DATABASE_URL=postgresql://user:password@host:5432/dbname  # From Step 1
SECRET_KEY=<generate-a-random-secret-key>
DEBUG=False
ALLOWED_HOSTS=*.onrender.com,your-custom-domain.com
CSRF_TRUSTED_ORIGINS=https://*.onrender.com,https://your-custom-domain.com
```

#### Email Configuration (Brevo):
```bash
EMAIL_BACKEND=blood_donation.email_backend.BrevoAPIEmailBackend
BREVO_API_KEY=xkeysib-your-brevo-api-key-here
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
DEFAULT_FROM_EMAIL_NAME=BloodLife Platform
```

#### Optional Variables:
```bash
# Google Maps (optional - app works without it using OpenStreetMap)
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# Auto-create admin user (set to true initially, then disable)
CREATE_SUPERUSER=true
SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@yourdomain.com
SUPERUSER_PASSWORD=secure-password-here

# Celery (set to eager mode for free tier - no Redis needed)
CELERY_TASK_ALWAYS_EAGER=True
```

### Step 4: Deploy

1. Click "Create Web Service"
2. Monitor the build logs
3. Wait for deployment to complete
4. Your app will be live at: `https://your-app-name.onrender.com`

---

## 🔑 Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | ✅ | Django secret key (use long random string) | `django-insecure-xyz...` |
| `DEBUG` | ✅ | Set to False in production | `False` |
| `ALLOWED_HOSTS` | ✅ | Comma-separated allowed domains | `*.onrender.com,localhost` |
| `CSRF_TRUSTED_ORIGINS` | ✅ | Comma-separated trusted origins | `https://*.onrender.com` |
| `BREVO_API_KEY` | ✅ | Brevo email API key | `xkeysib-...` |
| `DEFAULT_FROM_EMAIL` | ✅ | Sender email address | `noreply@yourdomain.com` |
| `GOOGLE_MAPS_API_KEY` | ❌ | Google Maps API (optional) | `AIza...` |
| `REDIS_URL` | ❌ | Redis URL (not needed with CELERY_TASK_ALWAYS_EAGER) | `redis://...` |
| `CELERY_TASK_ALWAYS_EAGER` | ❌ | Run tasks synchronously | `True` |

---

## 🗄️ Database Setup

### Automatic Migrations

The `Procfile` includes a release command that runs migrations automatically:
```
release: python manage.py migrate --noinput
```

### Create Superuser (Optional)

To create an admin user after deployment:

**Method 1: Environment Variables**
Set these in Render dashboard:
```bash
CREATE_SUPERUSER=true
SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@example.com
SUPERUSER_PASSWORD=secure-password
```

**Method 2: Render Shell**
1. Go to your service dashboard
2. Click "Shell" tab
3. Run:
   ```bash
   python manage.py createsuperuser
   ```

---

## 📧 Email Configuration

### Using Brevo (Recommended for Render)

1. **Sign up for Brevo** at [brevo.com](https://www.brevo.com)
2. **Verify your domain** in Brevo dashboard
3. **Get API Key**:
   - Go to Profile → SMTP & API → API Keys
   - Create a new API key (starts with `xkeysib-`)
4. **Set in Render**:
   ```bash
   BREVO_API_KEY=xkeysib-your-api-key-here
   DEFAULT_FROM_EMAIL=verified-email@yourdomain.com
   ```

### Alternative: SMTP

If you prefer SMTP (Gmail, etc.):
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

## 🐛 Troubleshooting

### Build Fails

**Issue**: `render_build.sh: Permission denied`
**Solution**: Make the script executable
```bash
git update-index --chmod=+x render_build.sh
git commit -m "Make render_build.sh executable"
git push
```

**Issue**: `ModuleNotFoundError: No module named 'blood_donation'`
**Solution**: Ensure `DJANGO_SETTINGS_MODULE=blood_donation.settings` is set

**Issue**: `psycopg2 installation failed`
**Solution**: The build script handles this. Check logs for missing system dependencies.

### Database Connection Errors

**Issue**: `could not connect to server`
**Solutions**:
1. Verify `DATABASE_URL` is correct
2. Ensure database and web service are in the same region
3. Check if database is still running (free tier spins down)

**Issue**: `relation does not exist`
**Solution**: Run migrations manually via Render Shell:
```bash
python manage.py migrate
```

### Static Files Not Loading

**Issue**: CSS/JS files return 404
**Solutions**:
1. Check build logs for `collectstatic` success
2. Verify `WHITENOISE_USE_FINDERS=False` in settings
3. Clear browser cache

### Email Not Sending

**Issue**: Emails not delivered
**Solutions**:
1. Verify `BREVO_API_KEY` is correct and starts with `xkeysib-`
2. Ensure sender email is verified in Brevo
3. Check Render logs for email errors

---

## 🎉 Post-Deployment

### 1. Test Your Application

Visit your deployed URL and test:
- ✅ User registration
- ✅ Login/logout
- ✅ Creating blood requests
- ✅ Email notifications
- ✅ Admin panel (`/secure-admin-panel-x92/`)

### 2. Set Up Custom Domain (Optional)

1. Go to your service dashboard
2. Click "Settings" → "Custom Domains"
3. Add your domain
4. Update DNS records as instructed
5. Update environment variables:
   ```bash
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,*.onrender.com
   CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

### 3. Monitor Your Application

- **Logs**: Dashboard → "Logs" tab
- **Metrics**: Dashboard → "Metrics" tab
- **Health Check**: Visit `https://your-app.onrender.com/health/`

### 4. Set Up Monitoring (Optional)

Add Sentry for error tracking:
```bash
pip install sentry-sdk
```

Add to `settings.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
)
```

---

## 🔄 Updating Your Application

After making changes:

```bash
git add .
git commit -m "Update description"
git push origin main
```

Render will automatically:
1. Detect the push
2. Run `render_build.sh`
3. Collect static files
4. Run migrations
5. Deploy the new version

---

## 📊 Free Tier Limitations

**Render Free Tier**:
- Web services spin down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds
- PostgreSQL database expires after 90 days
- 750 hours/month limit (enough for one always-on service)

**Workarounds**:
- Use a monitoring service (UptimeRobot) to ping your app every 14 minutes
- Upgrade to paid plan for production ($7/month)

---

## 🆘 Need Help?

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Django Docs**: [docs.djangoproject.com](https://docs.djangoproject.com)
- **Issues**: Check your Render service logs for detailed error messages

---

## ✅ Deployment Checklist

Before going live:

- [ ] PostgreSQL database created and connected
- [ ] All environment variables set
- [ ] `DEBUG=False` in production
- [ ] `SECRET_KEY` is a strong, random value
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] Email service configured and tested
- [ ] Migrations ran successfully
- [ ] Superuser created
- [ ] Static files loading correctly
- [ ] Health check endpoint working (`/health/`)
- [ ] Custom domain configured (optional)
- [ ] SSL/HTTPS enabled (automatic on Render)

---

**Congratulations! 🎉 Your BloodLife Platform is now live on Render!**
