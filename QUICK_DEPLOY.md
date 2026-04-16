# 🚀 Quick Start - Deploy to Render in 10 Minutes

## Option 1: Automatic Deploy (Fastest) ⚡

### 1. Push to GitHub
```bash
cd blood-donation-help
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 2. Deploy on Render
1. Go to [render.com](https://render.com) and sign in
2. Click **New +** → **Blueprint**
3. Connect your GitHub repository
4. Render auto-detects `render.yaml`
5. Fill in required environment variables:
   - `BREVO_API_KEY` - Get from [brevo.com](https://www.brevo.com)
   - `REDIS_URL` - Optional (leave blank for free tier)
   - `GOOGLE_MAPS_API_KEY` - Optional
6. Click **Apply**
7. Wait 5-10 minutes ✅

**Your app is live at:** `https://bloodlife-platform-xxxx.onrender.com`

---

## Option 2: Manual Deploy 🔧

### Step-by-Step (5 steps):

#### 1️⃣ Create PostgreSQL Database
- Render Dashboard → New + → PostgreSQL
- Name: `bloodlife-db`
- Copy the **Internal Database URL**

#### 2️⃣ Create Web Service
- New + → Web Service
- Connect GitHub repo
- **Build Command**: `./render_build.sh`
- **Start Command**: `gunicorn blood_donation.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120`

#### 3️⃣ Set Environment Variables
Go to Environment tab and add:

```
DJANGO_SETTINGS_MODULE = blood_donation.settings
DATABASE_URL = <paste from step 1>
SECRET_KEY = <generate random string>
DEBUG = False
ALLOWED_HOSTS = *.onrender.com,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS = https://*.onrender.com
BREVO_API_KEY = xkeysib-your-key-here
DEFAULT_FROM_EMAIL = noreply@yourdomain.com
CELERY_TASK_ALWAYS_EAGER = True
```

#### 4️⃣ Deploy
- Click **Create Web Service**
- Wait for build to complete
- Test your app! 🎉

#### 5️⃣ Create Admin User
- Go to Shell tab in Render dashboard
- Run: `python manage.py createsuperuser`
- Access admin at: `https://your-app.onrender.com/secure-admin-panel-x92/`

---

## ✅ Verify Deployment

Test these URLs:
- Homepage: `https://your-app.onrender.com/`
- Health Check: `https://your-app.onrender.com/health/`
- Admin: `https://your-app.onrender.com/secure-admin-panel-x92/`
- API: `https://your-app.onrender.com/api/v2/health/`

---

## 🐛 Common Issues

| Problem | Solution |
|---------|----------|
| Build fails | Check logs, ensure `render_build.sh` is executable |
| Database error | Verify `DATABASE_URL` is correct |
| 500 error | Check logs, ensure all env vars are set |
| Static files 404 | Wait for build to complete, check `collectstatic` in logs |
| Email not working | Verify `BREVO_API_KEY` starts with `xkeysib-` |

---

## 📚 Need More Help?

- Full Guide: See `RENDER_DEPLOYMENT_GUIDE.md`
- Render Docs: [render.com/docs](https://render.com/docs)
- Check Logs: Dashboard → Logs tab

---

**That's it! Your BloodLife platform is now live! 🎊**
