"""
Notification system for blood donation reminders and updates
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Notification(models.Model):
    """
    System notifications for users
    Enhanced with priority, category, and tracking
    """
    NOTIFICATION_TYPES = [
        ('donation_reminder', 'Donation Reminder'),
        ('blood_request', 'Blood Request Alert'),
        ('status_update', 'Status Update Required'),
        ('eligibility', 'Eligibility Notice'),
        ('general', 'General Announcement'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    CATEGORY_CHOICES = [
        ('medical', 'Medical'),
        ('system', 'System'),
        ('social', 'Social'),
        ('reminder', 'Reminder'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    related_request = models.ForeignKey(
        'blood_requests_app.BloodRequest',
        on_delete=models.SET_NULL,
        related_name='notifications',
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_read(self):
        """Mark notification as read and update real-time count"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
        
        # Update real-time notification count via WebSocket
        try:
            from .consumers import broadcast_notification_update
            from asgiref.sync import async_to_sync
            
            # Send update to connected WebSocket clients
            async_to_sync(broadcast_notification_update)(self.user)
        except Exception:
            # If WebSocket not available, continue without error
            pass
    
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class DonationReminderManager:
    """
    Manager for handling donation reminders and eligibility checks
    """
    
    # Donation eligibility gaps (in months)
    MALE_GAP_MONTHS = 3
    FEMALE_GAP_MONTHS = 4
    
    @staticmethod
    def check_eligibility(user):
        """
        Check if user is eligible to donate blood again
        Returns dict with eligibility status and details
        """
        # Use User model's last_donation_date field directly
        last_donation = user.last_donation_date
        
        if not last_donation:
            return {
                'eligible': True,
                'reason': 'No previous donation recorded',
                'days_until_eligible': 0,
                'message': "You haven't recorded any donation yet. Please update your status! ❤️"
            }
        
        # Calculate gap (default to male gap of 3 months = 90 days)
        # Note: User model doesn't have gender field, using standard 90-day gap
        gap_days = 90
        
        try:
            # Handle both date objects and string dates
            from datetime import datetime
            if isinstance(last_donation, str):
                last_donation_date = datetime.strptime(last_donation, '%Y-%m-%d').date()
            else:
                last_donation_date = last_donation
            
            days_since_donation = (timezone.now().date() - last_donation_date).days
            days_until_eligible = gap_days - days_since_donation
            
            if days_until_eligible <= 0:
                return {
                    'eligible': True,
                    'reason': f'Last donation was {days_since_donation} days ago',
                    'days_until_eligible': 0,
                    'message': f"Great news! You're eligible to donate blood again. It's been {days_since_donation} days since your last donation. ❤️"
                }
            else:
                return {
                    'eligible': False,
                    'reason': f'Last donation was {days_since_donation} days ago',
                    'days_until_eligible': days_until_eligible,
                    'message': f"You need to wait {days_until_eligible} more days before your next donation."
                }
        except (ValueError, TypeError) as e:
            return {
                'eligible': True,
                'reason': f'Error parsing donation date: {str(e)}',
                'days_until_eligible': 0,
                'message': "Please update your donation status! ❤️"
            }
    
    @staticmethod
    def should_show_update_popup(user):
        """
        Check if we should show the status update popup
        Returns True if user hasn't updated today
        """
        try:
            # Use DonorAvailability model which has last_status_update field
            from donors.models import DonorAvailability
            availability = DonorAvailability.objects.get(donor=user)
            
            # Check if last_status_update is today
            if availability.last_status_update == timezone.now().date():
                return False
            
            return True
        except DonorAvailability.DoesNotExist:
            # If no availability record exists, show the popup
            return True
        except Exception:
            return True
    
    @staticmethod
    def create_donation_reminder(user):
        """
        Create a donation reminder notification for user
        """
        eligibility = DonationReminderManager.check_eligibility(user)
        
        if eligibility['eligible']:
            notification = Notification.objects.create(
                user=user,
                notification_type='donation_reminder',
                title="Time to Donate Again! ❤️",
                message=eligibility['message'],
                expires_at=timezone.now() + timedelta(days=1)
            )
            return notification
        
        return None
