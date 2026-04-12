from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_password_reset_email_task(self, user_email, user_name, otp):
    """Celery task to send password reset email asynchronously using Brevo HTTP API"""
    try:
        subject = 'Password Reset OTP - Blood Donation Platform'
        html_message = f'''
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hello {user_name},</p>
            
            <p>You have requested to reset your password. Your One-Time Password (OTP) is:</p>
            
            <h1 style="color: #d32f2f; font-size: 2em;">{otp}</h1>
            
            <p><strong>This OTP will expire in 5 minutes.</strong></p>
            
            <p>If you did not request this password reset, please ignore this email.</p>
            
            <p>Best regards,<br>
            Blood Donation Platform Team</p>
        </body>
        </html>
        '''.strip()
        
        # Use explicit Brevo backend connection
        from django.core.mail import send_mail, get_connection
        
        connection = get_connection(
            backend='blood_donation.email_backend.BrevoAPIEmailBackend',
            fail_silently=False
        )
        
        # Use Django's send_mail with explicit Brevo connection
        send_mail(
            subject=subject,
            message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
            html_message=html_message,
            connection=connection
        )
        
        logger.info(f"✅ Password reset email sent successfully to {user_email} via Brevo HTTP API")
        return True
        
    except Exception as exc:
        logger.error(f"❌ Failed to send password reset email to {user_email}: {str(exc)}")
        logger.exception(exc)  # Log full traceback
        # Don't retry if it's a configuration issue
        if 'Connection refused' in str(exc) or 'BREVO_API_KEY' in str(exc):
            logger.error(f"Permanent error - not retrying: {str(exc)}")
            return False
        # Retry for temporary network issues
        raise self.retry(exc=exc)

@shared_task
def cleanup_expired_otps():
    """Celery task to clean up expired OTPs (run periodically)"""
    from .models import PasswordResetOTP
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        # Delete OTPs older than 10 minutes
        expired_time = timezone.now() - timedelta(minutes=10)
        deleted_count = PasswordResetOTP.objects.filter(
            created_at__lt=expired_time
        ).delete()[0]
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired OTPs")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired OTPs: {str(e)}")
        return 0