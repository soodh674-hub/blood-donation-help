# BloodLife - Modern React Web & Mobile App

## 🚀 Complete Setup Guide

This is a complete rewrite of BloodLife with:
- **React Web App** (for desktop/hospital PCs)
- **React Native Mobile App** (iOS & Android)
- **Django REST API Backend** (enhanced v2 API)

---

## 📋 Prerequisites

- Node.js 18+ and npm
- Python 3.10+ (already installed)
- Expo CLI (for mobile app)

---

## 🔧 Installation Steps

### 1. Install Web App Dependencies

```bash
cd frontend/web
npm install
```

### 2. Install Mobile App Dependencies

```bash
cd ../mobile
npm install
```

### 3. Start Django Backend

```bash
cd ../../  # Back to blood-donation-help root
python manage.py runserver
```

### 4. Start Web Development Server

```bash
cd frontend/web
npm run dev
```

Web app will be available at: http://localhost:3000

### 5. Start Mobile App (Expo)

```bash
cd ../mobile
npx expo start
```

Scan QR code with Expo Go app on your phone or press 'w' for web.

---

## 🏗️ Project Structure

```
blood-donation-help/
├── blood_donation/          # Django backend
│   ├── urls.py              # Main URL config (includes /api/v2/)
│   └── ...
├── blood_requests_app/
│   ├── api_enhanced.py      # NEW: Enhanced REST API endpoints
│   ├── api_urls_enhanced.py # NEW: API URL routing
│   └── ...
├── frontend/
│   ├── web/                 # React web app (Vite + TypeScript + Tailwind)
│   │   ├── src/
│   │   │   ├── components/  # Reusable UI components
│   │   │   ├── App.tsx      # Main app component
│   │   │   └── main.tsx     # Entry point
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   └── tailwind.config.js
│   └── mobile/              # React Native mobile app (Expo)
│       ├── app/             # Expo Router pages
│       └── package.json
└── ...
```

---

## ✨ Features Implemented

### Backend (Django)
✅ Enhanced REST API (`/api/v2/`)
✅ Dashboard statistics endpoint
✅ Live blood requests API
✅ Donor search with location
✅ Request tracking
✅ Notifications API
✅ Chat messages API
✅ User profile with donation history

### Web App (React)
✅ Modern dark theme UI
✅ Responsive design
✅ Live requests dashboard
✅ Donor search interface
✅ Stats display
✅ How it works section
✅ CTA sections

### Mobile App (React Native)
🔄 Setup ready (to be developed)

---

## 🎨 UI Design

The web app features:
- Dark gradient background (#0b1c2c → #111827)
- Red accent color (#ef4444)
- Modern cards with hover effects
- Responsive grid layout
- Professional typography

---

## 🔌 API Endpoints Available

All endpoints under `/api/v2/`:

- `GET /dashboard/stats/` - Dashboard statistics
- `GET /requests/live/` - Live blood requests
- `GET /donors/search/` - Search donors
- `GET /requests/{id}/track/` - Track specific request
- `GET /notifications/` - User notifications
- `POST /notifications/` - Mark as read
- `GET /requests/{id}/chat/` - Chat messages
- `GET /users/profile/` - User profile
- `POST /requests/create/` - Create blood request
- `GET /requests/my/` - My requests

---

## 🚀 Next Steps

1. Install dependencies (see above)
2. Test API endpoints
3. Build out remaining components
4. Implement authentication
5. Add real-time WebSocket support
6. Deploy to production

---

## 📝 Notes

- TypeScript errors in IDE are normal before `npm install`
- API proxy configured in Vite (web app → Django backend)
- Mobile app uses Expo for easy cross-platform development
- All API responses follow `{success: boolean, data: any}` format

---

## 🆘 Troubleshooting

**CORS Errors:**
Add `django-cors-headers` to Django if needed

**API Not Responding:**
Ensure Django server is running on port 8000

**Mobile App Won't Start:**
Install Expo CLI: `npm install -g expo-cli`

---

## 📞 Support

For issues or questions, check the Django logs and browser console.
