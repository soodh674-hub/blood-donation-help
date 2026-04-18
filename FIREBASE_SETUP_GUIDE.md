# Firebase Integration Guide for Blood Donation App

This guide will help you integrate Firebase for real-time chat and push notifications.

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" and create a new project
3. Enable Google Analytics (optional but recommended)
4. Wait for project to be created

## Step 2: Get Firebase Configuration

### For Web (JavaScript):
1. In Firebase Console, click the gear icon (Project Settings)
2. Scroll down to "Your apps" section
3. Click the web icon (`</>`) to add a web app
4. Register the app (name it "blood-donation-web")
5. Copy the Firebase configuration object - it looks like:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};
```

### For Python (Admin SDK):
1. In Firebase Console, go to Project Settings > Service Accounts
2. Click "Generate new private key"
3. Download the JSON file
4. Rename it to `firebase-service-account.json`
5. Move it to your project root (same level as manage.py)
6. **IMPORTANT:** Never commit this file to Git! Add it to `.gitignore`

## Step 3: Install Firebase SDKs

### Install Firebase Admin SDK for Python:
```bash
pip install firebase-admin
```

### Add to requirements.txt:
```
firebase-admin==6.4.0
```

## Step 4: Update Django Settings

The Firebase configuration has already been added to `blood_donation/settings.py`. Update it with your actual credentials:

```python
# Firebase Configuration
FIREBASE_API_KEY = 'YOUR_API_KEY'
FIREBASE_AUTH_DOMAIN = 'YOUR_PROJECT_ID.firebaseapp.com'
FIREBASE_PROJECT_ID = 'YOUR_PROJECT_ID'
FIREBASE_STORAGE_BUCKET = 'YOUR_PROJECT_ID.appspot.com'
FIREBASE_MESSAGING_SENDER_ID = 'YOUR_SENDER_ID'
FIREBASE_APP_ID = 'YOUR_APP_ID'

# Firebase Admin SDK (for backend operations)
FIREBASE_SERVICE_ACCOUNT_KEY = os.path.join(BASE_DIR, 'firebase-service-account.json')
```

## Step 5: Add Firebase to Frontend

Add this to your base template (`templates/base.html`) before the closing `</body>` tag:

```html
<!-- Firebase SDK -->
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-database-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.22.0/firebase-messaging-compat.js"></script>

<script>
    // Initialize Firebase
    const firebaseConfig = {
        apiKey: "{{ settings.FIREBASE_API_KEY }}",
        authDomain: "{{ settings.FIREBASE_AUTH_DOMAIN }}",
        projectId: "{{ settings.FIREBASE_PROJECT_ID }}",
        storageBucket: "{{ settings.FIREBASE_STORAGE_BUCKET }}",
        messagingSenderId: "{{ settings.FIREBASE_MESSAGING_SENDER_ID }}",
        appId: "{{ settings.FIREBASE_APP_ID }}"
    };

    firebase.initializeApp(firebaseConfig);
</script>
```

## Step 6: Enable Firebase Services in Console

### Enable Realtime Database:
1. Go to Firebase Console > Realtime Database
2. Click "Create Database"
3. Select a location (choose closest to your users)
4. Start in test mode (for development)
5. Set security rules (later)

### Enable Cloud Messaging:
1. Go to Firebase Console > Cloud Messaging
2. It's usually enabled by default
3. You'll need to add FCM server key for backend

## Step 7: Create Firebase Service Module

Create `blood_requests_app/firebase_service.py`:

```python
import firebase_admin
from firebase_admin import credentials, db, messaging
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
    firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}")

def send_push_notification(user_fcm_token, title, body, data=None):
    """Send push notification using FCM"""
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=user_fcm_token,
            data=data or {}
        )
        
        response = messaging.send(message)
        logger.info(f"Push notification sent successfully: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        return False

def save_chat_message_to_firebase(request_id, sender_id, message):
    """Save chat message to Firebase Realtime Database"""
    try:
        ref = db.reference(f'chats/{request_id}')
        new_message_ref = ref.push()
        new_message_ref.set({
            'sender_id': sender_id,
            'message': message,
            'timestamp': firebase_admin.db.ServerValue.TIMESTAMP
        })
        return new_message_ref.key
    except Exception as e:
        logger.error(f"Failed to save chat message to Firebase: {e}")
        return None

def listen_to_chat_messages(request_id, callback):
    """Listen to chat messages from Firebase (for WebSocket replacement)"""
    try:
        ref = db.reference(f'chats/{request_id}')
        ref.listen(callback)
    except Exception as e:
        logger.error(f"Failed to listen to Firebase messages: {e}")
```

## Step 8: Update User Model with FCM Token

The User model already has `fcm_token` field. You need to save the FCM token when users register or log in.

Add to your login/registration views:

```python
def save_fcm_token(request):
    """Save FCM token for push notifications"""
    fcm_token = request.POST.get('fcm_token')
    if fcm_token:
        request.user.fcm_token = fcm_token
        request.user.save()
```

## Step 9: Add Firebase Chat to Frontend

Add this JavaScript to your chat pages:

```javascript
// Send message to Firebase
async function sendFirebaseMessage(requestId, message) {
    const chatRef = firebase.database().ref(`chats/${requestId}`);
    await chatRef.push({
        sender_id: currentUser.id,
        message: message,
        timestamp: firebase.database.ServerValue.TIMESTAMP
    });
}

// Listen for new messages
function listenToMessages(requestId) {
    const chatRef = firebase.database().ref(`chats/${requestId}`);
    
    chatRef.on('child_added', (snapshot) => {
        const message = snapshot.val();
        displayMessage(message);
    });
}

// Request FCM permission and get token
async function requestNotificationPermission() {
    try {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            const token = await firebase.messaging().getToken();
            // Send token to backend
            await fetch('/api/save-fcm-token/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({fcm_token: token})
            });
        }
    } catch (error) {
        console.error('Notification permission error:', error);
    }
}
```

## Step 10: Security Rules for Firebase

In Firebase Console > Realtime Database > Rules, set:

```json
{
  "rules": {
    ".read": true,
    ".write": "auth != null",
    "chats": {
      "$requestId": {
        ".read": "auth != null",
        ".write": "auth != null"
      }
    }
  }
}
```

## Step 11: Test the Integration

1. Run the development server
2. Try sending a chat message
3. Check Firebase Console > Realtime Database to see messages
4. Test push notifications

## Troubleshooting

### Common Issues:

1. **"Firebase not defined" error**: Make sure Firebase SDK scripts are loaded before your custom scripts
2. **"Permission denied" error**: Check Firebase security rules
3. **FCM not working**: Make sure FCM token is saved correctly in User model
4. **Admin SDK initialization error**: Check that service account JSON file exists and is valid

## Next Steps

After basic integration:
- Implement real-time chat using Firebase listeners
- Add push notifications for blood request updates
- Sync chat messages between Firebase and Django database
- Add notification preferences in user settings
