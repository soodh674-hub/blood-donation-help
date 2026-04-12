"""
Django signals for automatic notification creation
Connects to user and blood request events to trigger notifications
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from blood_requests_app.models import BloodRequest
from notifications.services import NotificationService, BloodRequestNotificationService
from donors.models import DonorAvailability

User = get_user_model()


@receiver(post_save, sender=User)
def user_created_welcome_notification(sender, instance, created, **kwargs):
    """
    Send welcome notification when new user registers
    """
    if created:
        # Create welcome notification
        NotificationService.create_notification(
            user=instance,
            notification_type='general',
            title='🎉 Welcome to BloodLife!',
            message=(
                f"Welcome {instance.first_name or 'friend'}! You've successfully joined our "
                f"life-saving community. Complete your profile to start making a difference!"
            ),
            priority='medium',
            category='system',
            expires_hours=72
        )


@receiver(post_save, sender=BloodRequest)
def blood_request_donor_notifications(sender, instance, created, **kwargs):
    """
    Send notifications to eligible donors when new blood request is created
    Uses enhanced blood group compatibility matching
    """
    if created:
        try:
            # Use enhanced notification service with blood group compatibility
            notifications_sent = BloodRequestNotificationService.send_blood_request_notification(instance)
            print(f"Blood request notifications sent: {notifications_sent} donors notified")

            # For emergency requests, send additional emergency notifications
            if instance.priority == 'emergency':
                emergency_sent = BloodRequestNotificationService.send_emergency_notification(instance)
                print(f"Emergency notifications sent: {emergency_sent} additional donors notified")

        except Exception as e:
            print(f"Error sending blood request notifications: {e}")


@receiver(post_save, sender=DonorAvailability)
def donor_availability_change_notification(sender, instance, **kwargs):
    """
    Send confirmation notification when donor updates availability
    """
    try:
        user = instance.donor
        
        if instance.is_available:
            title = '✅ Availability Status Updated'
            message = 'Your availability status has been updated. Thank you for being ready to help!'
        else:
            title = '📝 Status Updated'
            message = 'Your availability status has been updated. Mark yourself available when you can donate.'
        
        NotificationService.create_notification(
            user=user,
            notification_type='status_update',
            title=title,
            message=message,
            priority='low',
            category='system',
            expires_hours=24
        )
    except Exception as e:
        print(f"Error sending availability update notification: {e}")


# Signal to check eligibility daily (would be called by Celery beat)
def check_daily_eligibility_reminders():
    """
    Check all donors and send eligibility reminders
    This should be called by Celery beat daily
    """
    try:
        eligible_donors = User.objects.filter(
            user_type='donor',
            is_available=True,
            last_donation_date__isnull=False
        )
        
        today = timezone.now().date()
        
        for donor in eligible_donors:
            if donor.last_donation_date:
                days_since = (today - donor.last_donation_date).days
                
                # Send reminder on exact eligibility day (90 days)
                if days_since == 90:
                    NotificationService.notify_eligibility(donor)
                    
                # Send gentle reminder at 60 days
                elif days_since == 60:
                    NotificationService.create_notification(
                        user=donor,
                        notification_type='eligibility',
                        title='📅 Coming Up Soon',
                        message=f"You'll be eligible to donate blood in 30 days. Start preparing to make a difference!",
                        priority='low',
                        category='medical',
                        expires_hours=48
                    )
                    
    except Exception as e:
        print(f"Error in daily eligibility check: {e}")
