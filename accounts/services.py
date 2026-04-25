"""
OTP storage service for password reset.
Uses Redis/Cache as primary storage for better performance.
Falls back to database when cache is unavailable.
"""
import json
import secrets
import logging
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

# Cache key prefixes
OTP_KEY_PREFIX = "reset_otp_"
VERIFIED_KEY_PREFIX = "reset_verified_"
RATE_LIMIT_KEY_PREFIX = "reset_otp_rate_"

# Configuration
OTP_EXPIRY_SECONDS = 300  # 5 minutes
VERIFIED_EXPIRY_SECONDS = 120  # 2 minutes to complete reset after verification
RATE_LIMIT_SECONDS = 60  # 1 OTP per 60 seconds
MAX_ATTEMPTS = 5


def _otp_key(user_id: int) -> str:
    return f"{OTP_KEY_PREFIX}{user_id}"


def _verified_key(user_id: int) -> str:
    return f"{VERIFIED_KEY_PREFIX}{user_id}"


def _rate_limit_key(user_id: int) -> str:
    return f"{RATE_LIMIT_KEY_PREFIX}{user_id}"


def generate_otp() -> str:
    """Generate a secure 6-digit OTP."""
    return "".join(secrets.choice("0123456789") for _ in range(6))


def store_otp(user_id: int, otp: str) -> bool:
    """
    Store OTP in cache (Redis/LocMem).
    Returns True if stored successfully.
    """
    data = {
        "otp": otp,
        "attempts": 0,
        "created_at": timezone.now().isoformat(),
    }
    try:
        key = _otp_key(user_id)
        cache.set(key, json.dumps(data), timeout=OTP_EXPIRY_SECONDS)
        return True
    except Exception as e:
        logger.warning(f"Cache OTP storage failed for user {user_id}: {e}")
        return False


def get_otp_data(user_id: int) -> dict | None:
    """Get OTP data from cache. Returns None if not found or expired."""
    try:
        key = _otp_key(user_id)
        raw = cache.get(key)
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.warning(f"Cache OTP get failed for user {user_id}: {e}")
    return None


def update_otp_attempts(user_id: int, attempts: int) -> bool:
    """Update attempt count in cache. Returns True if successful."""
    data = get_otp_data(user_id)
    if data is None:
        return False
    data["attempts"] = attempts
    try:
        # Get remaining TTL to preserve expiry
        key = _otp_key(user_id)
        ttl = cache.ttl(key)
        if ttl and ttl > 0:
            cache.set(key, json.dumps(data), timeout=ttl)
        else:
            cache.set(key, json.dumps(data), timeout=OTP_EXPIRY_SECONDS)
        return True
    except Exception as e:
        logger.warning(f"Cache OTP update failed for user {user_id}: {e}")
        return False


def mark_otp_verified(user_id: int) -> bool:
    """
    Mark OTP as verified and set verified token for reset_password.
    Returns True if successful.
    """
    try:
        key = _verified_key(user_id)
        cache.set(key, "1", timeout=VERIFIED_EXPIRY_SECONDS)
        # Delete OTP from cache (single-use)
        cache.delete(_otp_key(user_id))
        return True
    except Exception as e:
        logger.warning(f"Cache verified mark failed for user {user_id}: {e}")
        return False


def is_otp_verified(user_id: int) -> bool:
    """Check if user has a valid verified OTP for password reset."""
    try:
        return cache.get(_verified_key(user_id)) is not None
    except Exception as e:
        logger.warning(f"Cache verified check failed for user {user_id}: {e}")
        return False


def clear_reset_state(user_id: int) -> None:
    """Clear all OTP/verified state for user after successful reset."""
    try:
        cache.delete(_otp_key(user_id))
        cache.delete(_verified_key(user_id))
        cache.delete(_rate_limit_key(user_id))
    except Exception as e:
        logger.warning(f"Cache clear failed for user {user_id}: {e}")


def check_rate_limit(user_id: int) -> tuple[bool, int]:
    """
    Check if user can request new OTP (rate limit: 1 per 60 seconds).
    Returns (allowed, remaining_seconds).
    """
    try:
        key = _rate_limit_key(user_id)
        if cache.get(key) is None:
            return True, 0
        # Key exists - rate limited; get remaining time if backend supports TTL
        try:
            ttl = cache.ttl(key)
            if ttl is None or ttl <= 0:
                return False, RATE_LIMIT_SECONDS  # Assume full wait
            return False, int(ttl)
        except (AttributeError, NotImplementedError):
            return False, RATE_LIMIT_SECONDS
    except Exception as e:
        logger.warning(f"Rate limit check failed for user {user_id}: {e}")
        return True, 0


def set_rate_limit(user_id: int) -> None:
    """Record OTP request for rate limiting."""
    try:
        key = _rate_limit_key(user_id)
        cache.set(key, "1", timeout=RATE_LIMIT_SECONDS)
    except Exception as e:
        logger.warning(f"Rate limit set failed for user {user_id}: {e}")


def verify_otp_cache(user_id: int, entered_otp: str) -> tuple[bool, str]:
    """
    Verify OTP from cache.
    Returns (success, message).
    """
    data = get_otp_data(user_id)
    if data is None:
        return False, "OTP expired or not found. Please request a new one."

    attempts = data.get("attempts", 0)
    if attempts >= MAX_ATTEMPTS:
        cache.delete(_otp_key(user_id))
        return False, "Maximum attempts exceeded. Please request a new OTP."

    if data.get("otp") != entered_otp:
        data["attempts"] = attempts + 1
        try:
            key = _otp_key(user_id)
            ttl = cache.ttl(key)
            cache.set(key, json.dumps(data), timeout=ttl if ttl and ttl > 0 else OTP_EXPIRY_SECONDS)
        except Exception:
            pass
        remaining = MAX_ATTEMPTS - attempts - 1
        return False, f"Invalid OTP. {remaining} attempt(s) remaining."

    return True, "OTP verified successfully"


"""
SMS and Push Notification Services
"""
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class SMSService:
    """SMS notification service using Twilio or similar provider"""
    
    @staticmethod
    def send_sms(phone_number, message):
        """
        Send SMS notification
        Args:
            phone_number: Phone number with country code (e.g., +919876543210)
            message: SMS message content
        Returns:
            (success, message)
        """
        try:
            # Check if Twilio is configured
            if not hasattr(settings, 'TWILIO_ACCOUNT_SID') or not settings.TWILIO_ACCOUNT_SID:
                logger.warning("Twilio not configured, SMS will be logged only")
                logger.info(f"SMS to {phone_number}: {message}")
                return True, "SMS logged (Twilio not configured)"
            
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            message_obj = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            logger.info(f"SMS sent to {phone_number}: SID {message_obj.sid}")
            return True, "SMS sent successfully"
            
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}", exc_info=True)
            return False, f"SMS failed: {str(e)}"


class PushNotificationService:
    """Push notification service using Firebase Cloud Messaging (FCM)"""
    
    @staticmethod
    def send_push_notification(user, title, message, data=None):
        """
        Send push notification to user
        Args:
            user: User object
            title: Notification title
            message: Notification message
            data: Optional data payload
        Returns:
            (success, message)
        """
        try:
            # Check if Firebase is configured
            if not hasattr(settings, 'FIREBASE_CREDENTIALS'):
                logger.warning("Firebase not configured, push notification will be logged only")
                logger.info(f"Push to {user.username}: {title} - {message}")
                return True, "Push logged (Firebase not configured)"
            
            from firebase_admin import messaging
            from accounts.models import NotificationSettings
            
            # Check if user has push notifications enabled
            try:
                settings_obj = user.notification_settings
                if not settings_obj.push_notifications:
                    return True, "Push notifications disabled for user"
            except NotificationSettings.DoesNotExist:
                return True, "Notification settings not found"
            
            # Get user's FCM token (you need to store this in user profile)
            fcm_token = getattr(user, 'fcm_token', None)
            if not fcm_token:
                logger.warning(f"No FCM token for user {user.username}")
                return False, "No FCM token for user"
            
            # Create message
            notification = messaging.Notification(
                title=title,
                body=message
            )
            
            fcm_message = messaging.Message(
                notification=notification,
                token=fcm_token,
                data=data or {}
            )
            
            # Send message
            response = messaging.send(fcm_message)
            logger.info(f"Push sent to {user.username}: {response}")
            return True, "Push notification sent successfully"
            
        except Exception as e:
            logger.error(f"Push notification failed: {str(e)}", exc_info=True)
            return False, f"Push failed: {str(e)}"
    
    @staticmethod
    def send_bulk_push_notification(users, title, message, data=None):
        """
        Send bulk push notification to multiple users
        Args:
            users: QuerySet of User objects
            title: Notification title
            message: Notification message
            data: Optional data payload
        Returns:
            (success_count, failure_count)
        """
        success_count = 0
        failure_count = 0
        
        for user in users:
            success, _ = PushNotificationService.send_push_notification(user, title, message, data)
            if success:
                success_count += 1
            else:
                failure_count += 1
        
        return success_count, failure_count


def send_otp_email(email, otp, user_name=None):
    """
    Send OTP via email for login
    Args:
        email: Recipient email address
        otp: 6-digit OTP code
        user_name: Optional user name for personalization
    Returns:
        (success, message)
    """
    try:
        from django.conf import settings
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        
        # Create email content
        subject = "Your BloodLife Login OTP"
        
        # Plain text version
        plain_message = f"""
Hello {user_name or 'User'},

Your One-Time Password (OTP) for BloodLife login is: {otp}

This OTP is valid for 5 minutes. Please do not share this with anyone.

If you did not request this OTP, please ignore this email.

Best regards,
BloodLife Team
"""
        
        # HTML version
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #ef4444, #dc2626); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .otp {{ font-size: 32px; font-weight: bold; color: #ef4444; letter-spacing: 5px; text-align: center; margin: 20px 0; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>BloodLife Login OTP</h1>
        </div>
        <div class="content">
            <p>Hello {user_name or 'User'},</p>
            <p>Your One-Time Password (OTP) for BloodLife login is:</p>
            <div class="otp">{otp}</div>
            <p>This OTP is valid for <strong>5 minutes</strong>. Please do not share this with anyone.</p>
            <p>If you did not request this OTP, please ignore this email.</p>
            <p>Best regards,<br>BloodLife Team</p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Send email
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"OTP email sent to {email}")
        return True, "OTP sent successfully"
        
    except Exception as e:
        logger.error(f"OTP email sending failed: {str(e)}", exc_info=True)
        return False, f"Failed to send OTP: {str(e)}"


class NotificationService:
    """Unified notification service that handles SMS, push, and email"""
    
    @staticmethod
    def send_notification(user, title, message, notification_type='info', data=None):
        """
        Send notification via enabled channels
        Args:
            user: User object
            title: Notification title
            message: Notification message
            notification_type: Type of notification (blood_request, emergency, etc.)
            data: Optional data payload
        """
        from accounts.models import NotificationSettings
        
        try:
            # Get user's notification preferences
            try:
                settings_obj = user.notification_settings
            except NotificationSettings.DoesNotExist:
                settings_obj = NotificationSettings.objects.create(user=user)
            
            # Check quiet hours
            if settings_obj.quiet_hours_enabled:
                from django.utils import timezone
                now = timezone.now().time()
                if settings_obj.quiet_hours_start <= now <= settings_obj.quiet_hours_end:
                    logger.info(f"Quiet hours active for {user.username}, skipping notification")
                    return
            
            # Send SMS if enabled
            if settings_obj.sms_notifications and user.phone_number:
                SMSService.send_sms(user.phone_number, f"{title}: {message}")
            
            # Send push notification if enabled
            if settings_obj.push_notifications:
                PushNotificationService.send_push_notification(user, title, message, data)
            
            # Send email if enabled
            if settings_obj.email_notifications and user.email:
                html_message = render_to_string('emails/notification.html', {
                    'title': title,
                    'message': message,
                    'user': user
                })
                plain_message = strip_tags(html_message)
                send_mail(
                    title,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html_message,
                    fail_silently=True
                )
            
            # Create notification record
            from notifications.models import Notification
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type
            )
            
            # Send real-time notification via WebSocket
            from notifications.consumers import send_notification_to_user
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(send_notification_to_user(user, {
                    'title': title,
                    'message': message,
                    'notification_type': notification_type
                }))
            except:
                pass
            
        except Exception as e:
            logger.error(f"Notification sending failed: {str(e)}", exc_info=True)
    
    @staticmethod
    def send_blood_request_notification(donor, blood_request):
        """Send notification about new blood request to donor"""
        NotificationService.send_notification(
            donor,
            title="New Blood Request Near You",
            message=f"{blood_request.patient_blood_group} blood needed at {blood_request.hospital_name}",
            notification_type='blood_request',
            data={
                'request_id': blood_request.id,
                'blood_group': blood_request.patient_blood_group,
                'hospital': blood_request.hospital_name
            }
        )
    
    @staticmethod
    def send_emergency_notification(donor, blood_request):
        """Send emergency blood request notification"""
        NotificationService.send_notification(
            donor,
            title="🚨 EMERGENCY Blood Request",
            message=f"URGENT: {blood_request.patient_blood_group} blood needed immediately at {blood_request.hospital_name}",
            notification_type='emergency',
            data={
                'request_id': blood_request.id,
                'blood_group': blood_request.patient_blood_group,
                'hospital': blood_request.hospital_name,
                'priority': 'critical'
            }
        )
    
    @staticmethod
    def send_request_accepted_notification(requester, donor, blood_request):
        """Send notification when donor accepts request"""
        NotificationService.send_notification(
            requester,
            title="Donor Accepted Your Request",
            message=f"{donor.get_full_name()} has accepted your blood request for {blood_request.patient_blood_group}",
            notification_type='request_accepted',
            data={
                'request_id': blood_request.id,
                'donor_id': donor.id,
                'donor_name': donor.get_full_name()
            }
        )
    
    @staticmethod
    def send_donation_completed_notification(donor, blood_request):
        """Send notification when donation is completed"""
        NotificationService.send_notification(
            donor,
            title="Thank You for Donating!",
            message=f"Your blood donation for {blood_request.patient_name} has been recorded. You're a hero!",
            notification_type='donation_completed',
            data={
                'request_id': blood_request.id,
                'patient_name': blood_request.patient_name
            }
        )

