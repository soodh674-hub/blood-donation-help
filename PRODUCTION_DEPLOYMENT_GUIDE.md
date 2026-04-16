# 🚀 BloodLife Platform - Production Deployment Guide

## Complete Step-by-Step Guide for Deploying to Render

---

## 📋 PREREQUISITES

### 1. Accounts Required
- ✅ **GitHub Account** - For code repository
- ✅ **Render Account** - https://render.com (Free tier available)
- ✅ **Google Cloud Account** - For Maps API
- ✅ **Brevo Account** - For email notifications (free tier: 300 emails/day)

### 2. Technologies Needed
- PostgreSQL database (Render provides free tier)
- Redis instance (Required for WebSockets - Render provides)
- Domain name (optional, can use Render subdomain)

---

## 🛠️ STEP 1: PREPARE YOUR CODE

### 1.1 Update requirements.txt
Ensure all dependencies are listed:
```bash
cd blood-donation-help
pip freeze > requirements.txt
```

**Required packages:**
```
Django>=4.2,<5.0
djangorestframework
django-cors-headers
channels>=4.0
channels-redis
daphne
psycopg2-binary
celery
redis
Pillow
python-dotenv
requests
```

### 1.2 Create .gitignore
Ensure sensitive files are not committed:
```
.env
__pycache__/
*.pyc
db.sqlite3
media/
staticfiles/
logs/
venv/
```

### 1.3 Test Locally First
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your values

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Run development server
python manage.py runserver
```

---

## 🗄️ STEP 2: SET UP DATABASE ON RENDER

### 2.1 Create PostgreSQL Database
1. Go to https://render.com/dashboard
2. Click **New +** → **PostgreSQL**
3. Configure:
   - **Name**: `bloodlife-db`
   - **Database**: `bloodlife_db`
   - **User**: `bloodlife_user`
   - **Region**: Choose closest to your users
   - **Plan**: Free (or paid for production)
4. Click **Create Database**
5. **Save the connection string** (Internal Database URL)

### 2.2 Database URL Format
```
postgresql://bloodlife_user:password@host:5432/bloodlife_db
```

---

## 🔴 STEP 3: SET UP REDIS ON RENDER

### 3.1 Create Redis Instance
1. Go to https://render.com/dashboard
2. Click **New +** → **Redis**
3. Configure:
   - **Name**: `bloodlife-redis`
   - **Region**: Same as database
   - **Plan**: Free (or paid)
4. Click **Create Redis**
5. **Save the Redis URL**

### 3.2 Redis URL Format
```
redis://default:password@host:6379
```

---

## 📧 STEP 4: SET UP EMAIL SERVICE (BREVO)

### 4.1 Create Brevo Account
1. Go to https://app.brevo.com/
2. Sign up for free account
3. Verify your email
4. Go to **Profile** → **SMTP & API** → **API Keys**
5. Click **Generate New API Key**
6. **Copy the API key** (starts with `xkeysib-`)

### 4.2 Configure Sender Email
1. Go to **Senders & IP** in Brevo dashboard
2. Add your domain email (e.g., `noreply@yourdomain.com`)
3. Verify the email address

---

## 🗺️ STEP 5: GET GOOGLE MAPS API KEY

### 5.1 Create Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Create new project: `BloodLife Platform`
3. Go to **APIs & Services** → **Library**

### 5.2 Enable Required APIs
Enable these APIs:
- ✅ **Maps JavaScript API**
- ✅ **Places API**
- ✅ **Geocoding API**
- ✅ **Geolocation API**

### 5.3 Create API Key
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **API Key**
3. **Copy the API key**
4. **Restrict the key** (recommended):
   - HTTP referrers: `*.yourdomain.com`
   - Enable APIs: Maps JavaScript, Places, Geocoding

---

## 🌐 STEP 6: DEPLOY TO RENDER

### 6.1 Push Code to GitHub
```bash
# Initialize git (if not done)
git init
git add .
git commit -m "Initial commit - BloodLife Platform"

# Create repository on GitHub
# Then push:
git remote add origin https://github.com/yourusername/bloodlife.git
git push -u origin main
```

### 6.2 Create Web Service on Render
1. Go to https://render.com/dashboard
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `bloodlife-platform`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: `blood-donation-help` (if monorepo)
   - **Runtime**: `Python 3`
   - **Build Command**: `./render_build.sh`
   - **Start Command**: `daphne -b 0.0.0.0 -p $PORT blood_donation.asgi:application`
   - **Plan**: Free (or paid)

### 6.3 Add Environment Variables
In Render dashboard → Web Service → Environment:

**Required Variables:**
```
SECRET_KEY=<generate-secure-key>
DATABASE_URL=<postgresql-url-from-step-2>
REDIS_URL=<redis-url-from-step-3>
GOOGLE_MAPS_API_KEY=<google-maps-key-from-step-5>
BREVO_API_KEY=<brevo-api-key-from-step-4>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
DEFAULT_FROM_EMAIL_NAME=BloodLife Platform
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com,*.onrender.com
CSRF_TRUSTED_ORIGINS=https://your-app-name.onrender.com
```

**Generate SECRET_KEY:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6.4 Deploy
1. Click **Create Web Service**
2. Wait for build to complete (~5-10 minutes)
3. Check logs for any errors
4. Visit your app URL: `https://your-app-name.onrender.com`

---

## ⚙️ STEP 7: POST-DEPLOYMENT SETUP

### 7.1 Run Migrations
```bash
# In Render web shell or via SSH
python manage.py migrate
```

### 7.2 Create Superuser
```bash
python manage.py createsuperuser
```

Or set environment variables:
```
CREATE_SUPERUSER=true
SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@yourdomain.com
SUPERUSER_PASSWORD=secure-password
```

### 7.3 Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 7.4 Test All Features
- ✅ User registration
- ✅ Login/logout
- ✅ Create blood request
- ✅ Donor matching
- ✅ Chat messaging (WebSocket)
- ✅ Notifications
- ✅ Settings page
- ✅ Anonymous mode
- ✅ Google Maps integration

---

## 🔧 STEP 8: CONFIGURE CELERY WORKER (Optional)

For background tasks (email notifications, etc.):

### 8.1 Create Worker Service on Render
1. Go to Render dashboard
2. Click **New +** → **Background Worker**
3. Connect same repository
4. Configure:
   - **Name**: `bloodlife-celery`
   - **Build Command**: `./render_build.sh`
   - **Start Command**: `celery -A blood_donation worker -l info`
5. Add same environment variables

---

## 📊 STEP 9: MONITORING & LOGS

### 9.1 Enable Logging
In Render dashboard → Web Service → Logs:
- View real-time logs
- Download log files
- Set up log drains (optional)

### 9.2 Set Up Error Tracking (Optional)
- **Sentry**: https://sentry.io (Free tier available)
- Add to requirements.txt: `sentry-sdk`
- Configure in settings.py

### 9.3 Monitor Database
- Render dashboard → PostgreSQL → Metrics
- Monitor connections, storage, CPU

---

## 🔒 STEP 10: SECURITY HARDENING

### 10.1 Enable HTTPS
Render provides free SSL certificates automatically.

### 10.2 Configure Security Headers
Already set in `.env.example`:
```
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

### 10.3 Set Up CORS (if needed)
```
CORS_ALLOWED_ORIGINS=https://your-frontend.com
CORS_ALLOW_CREDENTIALS=True
```

### 10.4 Regular Backups
- Render provides automatic database backups
- Download backups regularly
- Test backup restoration

---

## 🚨 TROUBLESHOOTING

### Issue: Build Fails
**Check:**
- requirements.txt has all dependencies
- render_build.sh is executable: `chmod +x render_build.sh`
- Python version is correct (3.8+)

### Issue: Database Connection Error
**Check:**
- DATABASE_URL is correct
- PostgreSQL instance is running
- Credentials are valid

### Issue: WebSocket Not Working
**Check:**
- Redis instance is running
- CHANNEL_LAYERS is configured correctly
- ASGI application is set up
- Using `daphne` as ASGI server

### Issue: Email Not Sending
**Check:**
- BREVO_API_KEY is valid
- Sender email is verified in Brevo
- Check logs for error messages

### Issue: Static Files Not Loading
**Check:**
- STATIC_ROOT is set correctly
- collectstatic ran successfully
- DEBUG=False in production

---

## 📈 PERFORMANCE OPTIMIZATION

### 1. Database Optimization
- Add database indexes (already done)
- Use connection pooling (PgBouncer)
- Regular database maintenance

### 2. Caching
- Enable Redis caching
- Cache frequently accessed data
- Use Django's cache framework

### 3. Static Files
- Use CDN (CloudFlare free tier)
- Enable compression
- Set proper cache headers

### 4. WebSockets
- Use Redis channel layer (already configured)
- Monitor WebSocket connections
- Implement connection limits

---

## 🔄 DEPLOYMENT WORKFLOW

### For Updates:
```bash
# 1. Make changes locally
# 2. Test thoroughly
# 3. Commit and push
git add .
git commit -m "Update description"
git push origin main

# 4. Render auto-deploys
# 5. Monitor logs for errors
# 6. Test on production
```

### Rollback (if needed):
1. Go to Render dashboard
2. Click on deployment
3. Click **Rollback**
4. Select previous deployment

---

## 📝 ENVIRONMENT VARIABLES CHECKLIST

### Critical (Must Set):
- [x] SECRET_KEY
- [x] DATABASE_URL
- [x] DEBUG=False
- [x] ALLOWED_HOSTS

### Recommended:
- [x] GOOGLE_MAPS_API_KEY
- [x] BREVO_API_KEY
- [x] REDIS_URL
- [x] DEFAULT_FROM_EMAIL

### Optional:
- [ ] TWILIO_ACCOUNT_SID (SMS)
- [ ] FIREBASE credentials (Push notifications)
- [ ] AWS credentials (S3 storage)
- [ ] Sentry DSN (Error tracking)

---

## 🎯 FINAL CHECKLIST

Before going live:
- [ ] All environment variables set
- [ ] Database migrations run
- [ ] Static files collected
- [ ] Superuser created
- [ ] Email sending tested
- [ ] WebSocket connections working
- [ ] Google Maps loading
- [ ] All features tested
- [ ] Error pages customized
- [ ] SSL certificate active
- [ ] Backups configured
- [ ] Monitoring set up
- [ ] Domain configured (optional)

---

## 🆘 SUPPORT & RESOURCES

### Documentation:
- Django: https://docs.djangoproject.com/
- Django Channels: https://channels.readthedocs.io/
- Render: https://render.com/docs
- Brevo: https://developers.brevo.com/
- Google Maps: https://developers.google.com/maps

### Community:
- Django Forum: https://forum.djangoproject.com/
- Stack Overflow: #django tag
- Render Community: https://community.render.com/

---

**Deployment Time**: ~30-45 minutes
**Cost (Free Tier)**: $0 (with limitations)
**Cost (Production)**: ~$20-50/month (depends on traffic)

---

*Last Updated: Current Session*
*Version: 1.0*
*Status: Ready for Production*
