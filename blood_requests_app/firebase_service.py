"""
Firebase Service Module for Blood Donation App
Handles Firebase operations for real-time chat and push notifications
"""
import firebase_admin
from firebase_admin import credentials, db, messaging
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
_firebase_initialized = False

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    global _firebase_initialized
    if _firebase_initialized:
        return True
    
    try:
        if os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_KEY):
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            logger.info("✅ Firebase Admin SDK initialized successfully")
            return True
        else:
            logger.warning(f"⚠️ Firebase service account key not found at {settings.FIREBASE_SERVICE_ACCOUNT_KEY}")
            logger.warning("Firebase features will be limited. Download the key from Firebase Console > Project Settings > Service Accounts")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase: {e}")
        return False

def send_push_notification(user_fcm_token, title, body, data=None):
    """Send push notification using FCM"""
    if not initialize_firebase():
        logger.warning("Firebase not initialized, skipping push notification")
        return False
    
    try:
        if not user_fcm_token:
            logger.warning("No FCM token provided")
            return False
        
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=user_fcm_token,
            data=data or {}
        )
        
        response = messaging.send(message)
        logger.info(f"✅ Push notification sent successfully: {response}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send push notification: {e}")
        return False

def send_push_notification_to_topic(topic, title, body, data=None):
    """Send push notification to a topic (for broadcasting)"""
    if not initialize_firebase():
        logger.warning("Firebase not initialized, skipping topic notification")
        return False
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            topic=topic,
            data=data or {}
        )
        
        response = messaging.send(message)
        logger.info(f"✅ Topic notification sent successfully: {response}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send topic notification: {e}")
        return False

def save_chat_message_to_firebase(request_id, sender_id, message, sender_name=None):
    """Save chat message to Firebase Realtime Database"""
    if not initialize_firebase():
        logger.warning("Firebase not initialized, skipping Firebase chat save")
        return None
    
    try:
        ref = db.reference(f'chats/{request_id}')
        new_message_ref = ref.push()
        message_data = {
            'sender_id': sender_id,
            'message': message,
            'timestamp': firebase_admin.db.ServerValue.TIMESTAMP
        }
        if sender_name:
            message_data['sender_name'] = sender_name
        
        new_message_ref.set(message_data)
        logger.info(f"✅ Chat message saved to Firebase for request {request_id}")
        return new_message_ref.key
    except Exception as e:
        logger.error(f"❌ Failed to save chat message to Firebase: {e}")
        return None

def get_chat_messages_from_firebase(request_id, limit=50):
    """Get chat messages from Firebase Realtime Database"""
    if not initialize_firebase():
        logger.warning("Firebase not initialized, returning empty messages list")
        return []
    
    try:
        ref = db.reference(f'chats/{request_id}')
        messages = ref.order_by_key().limit_to_last(limit).get()
        
        if messages:
            return [
                {
                    'id': key,
                    'sender_id': msg.get('sender_id'),
                    'message': msg.get('message'),
                    'sender_name': msg.get('sender_name'),
                    'timestamp': msg.get('timestamp')
                }
                for key, msg in messages.items()
            ]
        return []
    except Exception as e:
        logger.error(f"❌ Failed to get chat messages from Firebase: {e}")
        return []

def subscribe_user_to_topic(user_fcm_token, topic):
    """Subscribe a user to a topic for notifications"""
    if not initialize_firebase():
        logger.warning("Firebase not initialized, skipping topic subscription")
        return False
    
    try:
        response = messaging.subscribe_to_topic([user_fcm_token], topic)
        logger.info(f"✅ User subscribed to topic {topic}: {response}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to subscribe user to topic: {e}")
        return False

def unsubscribe_user_from_topic(user_fcm_token, topic):
    """Unsubscribe a user from a topic"""
    if not initialize_firebase():
        logger.warning("Firebase not initialized, skipping topic unsubscription")
        return False
    
    try:
        response = messaging.unsubscribe_from_topic([user_fcm_token], topic)
        logger.info(f"✅ User unsubscribed from topic {topic}: {response}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to unsubscribe user from topic: {e}")
        return False

def notify_new_blood_request(request_id, blood_group, city, priority):
    """Notify matching donors about new blood request"""
    if not initialize_firebase():
        logger.warning("Firebase not initialized, skipping blood request notification")
        return False
    
    try:
        topic = f"blood_{blood_group}_{city.lower()}"
        title = f"🩸 Urgent Blood Required: {blood_group}"
        body = f"A new blood request in {city}. Priority: {priority}"
        
        data = {
            'type': 'blood_request',
            'request_id': str(request_id),
            'blood_group': blood_group,
            'city': city,
            'priority': priority
        }
        
        return send_push_notification_to_topic(topic, title, body, data)
    except Exception as e:
        logger.error(f"❌ Failed to notify about blood request: {e}")
        return False

def notify_donor_accepted(request_id, donor_name, requester_fcm_token):
    """Notify requester that a donor accepted their request"""
    if not requester_fcm_token:
        return False
    
    try:
        title = "✅ Donor Accepted Your Request"
        body = f"{donor_name} has accepted your blood request. You can now chat to coordinate."
        data = {
            'type': 'donor_accepted',
            'request_id': str(request_id),
            'donor_name': donor_name
        }
        
        return send_push_notification(requester_fcm_token, title, body, data)
    except Exception as e:
        logger.error(f"❌ Failed to notify about donor acceptance: {e}")
        return False

def notify_chat_message(request_id, sender_name, recipient_fcm_token):
    """Notify recipient about new chat message"""
    if not recipient_fcm_token:
        return False
    
    try:
        title = f"💬 New message from {sender_name}"
        body = "You have a new message regarding your blood request."
        data = {
            'type': 'chat_message',
            'request_id': str(request_id),
            'sender_name': sender_name
        }
        
        return send_push_notification(recipient_fcm_token, title, body, data)
    except Exception as e:
        logger.error(f"❌ Failed to notify about chat message: {e}")
        return False
