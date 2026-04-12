"""
Enhanced notification service with retry logic and error handling.
Provides reliable notification delivery with fallback mechanisms.
"""
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class NotificationService:
    """Advanced notification service with retry and fallback"""
    
    @staticmethod
    def send_email_notification(subject, message, recipient_list, html_message=None, fail_silently=True):
        """
        Send email notification with retry logic
        
        Args:
            subject: Email subject
            message: Plain text message
            recipient_list: List of recipient emails
            html_message: Optional HTML version
            fail_silently: Whether to suppress exceptions
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                sent_count = send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bloodis-life.online'),
                    recipient_list=recipient_list,
                    html_message=html_message,
                    fail_silently=fail_silently
                )
                
                if sent_count > 0:
                    logger.info(f"✅ Email sent successfully to {recipient_list}")
                    return True
                else:
                    logger.warning(f"⚠️ Email send returned 0 count for {recipient_list}")
                    
            except Exception as e:
                logger.error(f"❌ Email send attempt {attempt + 1}/{max_retries} failed: {e}")
                
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"❌ All {max_retries} email send attempts failed")
                    if not fail_silently:
                        raise
        
        return False
    
    @staticmethod
    def send_urgent_blood_request_alert(blood_request, donors):
        """
        Send urgent alerts to matched donors
        
        Args:
            blood_request: BloodRequest instance
            donors: QuerySet of matched donors
            
        Returns:
            dict: Results of notification attempts
        """
        results = {
            'emails_sent': 0,
            'emails_failed': 0,
            'errors': []
        }
        
        subject = f"🚨 URGENT: Blood Donation Needed - {blood_request.patient_blood_group}"
        
        message = f"""
Dear Donor,

An urgent blood donation request has been posted in your area.

Patient: {blood_request.patient_name}
Blood Group: {blood_request.patient_blood_group}
Hospital: {blood_request.hospital_name}
Location: {blood_request.city}, {blood_request.state}
Required By: {blood_request.required_by.strftime('%Y-%m-%d %H:%M')}
Priority: {blood_request.priority.upper()}

If you can donate, please visit our platform immediately to respond.

Every donation saves lives!

BloodLife Platform
        """
        
        html_message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #e53e3e, #c53030); color: white; padding: 20px; text-align: center;">
                <h1>🚨 URGENT BLOOD DONATION NEEDED</h1>
            </div>
            
            <div style="padding: 20px; background: #f7fafc;">
                <h2 style="color: #2d3748;">Request Details</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 8px;"><strong>Patient:</strong></td><td>{blood_request.patient_name}</td></tr>
                    <tr><td style="padding: 8px;"><strong>Blood Group:</strong></td><td style="color: #e53e3e; font-weight: bold;">{blood_request.patient_blood_group}</td></tr>
                    <tr><td style="padding: 8px;"><strong>Hospital:</strong></td><td>{blood_request.hospital_name}</td></tr>
                    <tr><td style="padding: 8px;"><strong>Location:</strong></td><td>{blood_request.city}, {blood_request.state}</td></tr>
                    <tr><td style="padding: 8px;"><strong>Required By:</strong></td><td>{blood_request.required_by.strftime('%Y-%m-%d %H:%M')}</td></tr>
                    <tr><td style="padding: 8px;"><strong>Priority:</strong></td><td style="color: #e53e3e; font-weight: bold;">{blood_request.priority.upper()}</td></tr>
                </table>
                
                <div style="margin-top: 20px; text-align: center;">
                    <a href="{settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://bloodis-life.online'}/requests/{blood_request.id}/" 
                       style="background: #e53e3e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Respond Now
                    </a>
                </div>
            </div>
            
            <div style="background: #edf2f7; padding: 15px; text-align: center; color: #718096; font-size: 12px;">
                <p>Every donation saves lives! Thank you for being a hero.</p>
            </div>
        </div>
        """
        
        donor_emails = []
        for donor in donors:
            if hasattr(donor, 'user') and donor.user.email:
                donor_emails.append(donor.user.email)
            elif hasattr(donor, 'email') and donor.email:
                donor_emails.append(donor.email)
        
        if not donor_emails:
            logger.warning("No valid donor emails found for blood request alert")
            return results
        
        # Send emails
        for email in donor_emails:
            try:
                success = NotificationService.send_email_notification(
                    subject=subject,
                    message=message,
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=True
                )
                
                if success:
                    results['emails_sent'] += 1
                else:
                    results['emails_failed'] += 1
            except Exception as e:
                results['emails_failed'] += 1
                results['errors'].append(str(e))
                logger.error(f"Failed to send email to {email}: {e}")
        
        logger.info(f"Blood request alert results: {results['emails_sent']} sent, {results['emails_failed']} failed")
        return results
    
    @staticmethod
    def send_donation_reminder(donation):
        """Send reminder for upcoming donation appointment"""
        try:
            subject = "Reminder: Your Blood Donation Appointment"
            
            message = f"""
Dear {donation.donor_name},

This is a friendly reminder about your upcoming blood donation appointment.

Date: {donation.scheduled_date.strftime('%Y-%m-%d')}
Time: {donation.scheduled_time if hasattr(donation, 'scheduled_time') else 'Contact hospital'}
Location: {donation.hospital_name}

Please remember to:
- Get a good night's sleep
- Eat a healthy meal before donating
- Drink plenty of water
- Bring a valid ID

Thank you for saving lives!

BloodLife Platform
            """
            
            if hasattr(donation, 'donor') and hasattr(donation.donor, 'user') and donation.donor.user.email:
                NotificationService.send_email_notification(
                    subject=subject,
                    message=message,
                    recipient_list=[donation.donor.user.email],
                    fail_silently=True
                )
        except Exception as e:
            logger.error(f"Failed to send donation reminder: {e}")
