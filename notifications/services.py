"""
Notification Service for Blood Request Alerts
Sends smart notifications to compatible donors based on blood group matching
"""
import logging
from django.db.models import Q
from django.utils import timezone
from accounts.models import User
from notifications.models import Notification
from donors.models import DonorAvailability

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Original notification service for general notifications
    Kept for backward compatibility with signals.py
    """
    
    @classmethod
    def create_notification(cls, user, notification_type, title, message, priority='medium', category='general', expires_hours=24):
        """
        Create a notification for a user
        """
        try:
            notification = Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                category=category,
                expires_at=timezone.now() + timezone.timedelta(hours=expires_hours) if expires_hours else None
            )
            logger.info(f'Notification created for user {user.id}: {title}')
            return notification
        except Exception as e:
            logger.error(f'Error creating notification: {str(e)}', exc_info=True)
            return None
    
    @classmethod
    def notify_blood_request(cls, donor, blood_request):
        """
        Send blood request notification to a donor
        """
        try:
            urgency_emoji = {'emergency': '🚨', 'urgent': '⚠️', 'normal': '📢'}.get(blood_request.priority, '📢')
            
            notification = cls.create_notification(
                user=donor,
                notification_type='blood_request',
                priority=blood_request.priority,
                category='medical',
                title=f'{urgency_emoji} {blood_request.get_priority_display()} Blood Needed - {blood_request.patient_blood_group}',
                message=(
                    f'Urgent blood request in {blood_request.city}! '
                    f'Patient needs {blood_request.required_units} unit(s) of {blood_request.patient_blood_group} blood. '
                    f'Hospital: {blood_request.hospital_name}. '
                    f'Contact: {blood_request.contact_phone or "Available on request"}'
                ),
                expires_hours=48
            )
            return notification
        except Exception as e:
            logger.error(f'Error notifying blood request: {str(e)}', exc_info=True)
            return None
    
    @classmethod
    def notify_eligibility(cls, donor):
        """
        Send eligibility reminder to donor
        """
        return cls.create_notification(
            user=donor,
            notification_type='eligibility',
            title='✅ Time to Donate Again!',
            message=f"You're eligible to donate blood. Your donation can save lives!",
            priority='medium',
            category='medical',
            expires_hours=72
        )


class BloodRequestNotificationService:
    """
    Enhanced service for sending blood request notifications to compatible donors
    Uses blood group compatibility matching
    """
    """
    Service for sending blood request notifications to compatible donors
    """
    
    # Blood group compatibility chart (who can donate to whom)
    BLOOD_COMPATIBILITY = {
        'A+': ['A+', 'AB+'],
        'A-': ['A+', 'A-', 'AB+', 'AB-'],
        'B+': ['B+', 'AB+'],
        'B-': ['B+', 'B-', 'AB+', 'AB-'],
        'AB+': ['AB+'],
        'AB-': ['AB+', 'AB-'],
        'O+': ['O+', 'A+', 'B+', 'AB+'],
        'O-': ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-'],  # Universal donor
    }
    
    @classmethod
    def get_compatible_donors(cls, patient_blood_group):
        """
        Get list of donors who can donate to a patient with given blood group
        Returns queryset of compatible users
        """
        if not patient_blood_group or patient_blood_group not in cls.BLOOD_COMPATIBILITY:
            return User.objects.none()
        
        # Get compatible blood groups (reverse lookup)
        compatible_groups = []
        for donor_group, compatible_recipients in cls.BLOOD_COMPATIBILITY.items():
            if patient_blood_group in compatible_recipients:
                compatible_groups.append(donor_group)
        
        logger.info(f'Compatible blood groups for {patient_blood_group}: {compatible_groups}')
        
        # Find donors with compatible blood groups who are available
        compatible_donors = User.objects.filter(
            blood_group__in=compatible_groups,
            user_type='donor',
            is_active=True
        ).exclude(
            Q(phone_number__isnull=True) | Q(phone_number='')
        )
        
        return compatible_donors
    
    @classmethod
    def send_blood_request_notification(cls, blood_request, limit=50):
        """
        Send blood request notifications to compatible donors
        Returns count of notifications sent
        """
        try:
            patient_blood_group = blood_request.patient_blood_group
            
            if not patient_blood_group:
                logger.warning('Blood request missing patient blood group')
                return 0
            
            # Get compatible donors
            compatible_donors = cls.get_compatible_donors(patient_blood_group)
            
            # Filter by location if available (city/pincode match)
            if blood_request.city:
                location_filtered = compatible_donors.filter(
                    Q(city=blood_request.city) | 
                    Q(pincode=blood_request.pincode[:3])  # First 3 digits
                )
                if location_filtered.exists():
                    compatible_donors = location_filtered
                    logger.info(f'Filtered donors by location: {blood_request.city}')
            
            # Limit number of notifications
            compatible_donors = compatible_donors[:limit]
            
            notifications_sent = 0
            
            # Determine urgency level
            urgency_level = blood_request.priority  # emergency, urgent, normal
            urgency_emoji = {'emergency': '🚨', 'urgent': '⚠️', 'normal': '📢'}.get(urgency_level, '📢')
            urgency_text = blood_request.get_priority_display()
            
            for donor in compatible_donors:
                # Check if donor is available
                try:
                    availability = DonorAvailability.objects.get(donor=donor)
                    if not availability.is_available:
                        continue
                except DonorAvailability.DoesNotExist:
                    pass  # Assume available if no record exists
                
                # Create notification
                notification = Notification.objects.create(
                    user=donor,
                    notification_type='blood_request',
                    priority=urgency_level,
                    category='medical',
                    title=f'{urgency_emoji} {urgency_text} Blood Needed - {patient_blood_group}',
                    message=(
                        f'Urgent blood request in {blood_request.city}! '
                        f'Patient needs {blood_request.required_units} unit(s) of {patient_blood_group} blood. '
                        f'Hospital: {blood_request.hospital_name}. '
                        f'Contact: {blood_request.contact_phone or "Available on request"}'
                    ),
                    expires_at=blood_request.expires_at
                )
                
                notifications_sent += 1
                logger.info(f'Blood request notification sent to donor {donor.id}')
            
            logger.info(f'Total notifications sent: {notifications_sent}')
            return notifications_sent
            
        except Exception as e:
            logger.error(f'Error sending blood request notifications: {str(e)}', exc_info=True)
            return 0
    
    @classmethod
    def send_emergency_notification(cls, blood_request):
        """
        Send emergency notification with higher priority
        Sends to more donors and marks as urgent
        """
        return cls.send_blood_request_notification(blood_request, limit=100)
    
    @staticmethod
    def should_notify_donor(donor, blood_request):
        """
        Check if donor should receive notification for this blood request
        Additional filters beyond blood compatibility
        """
        # Don't notify if donor is the requester
        if donor.id == blood_request.requester_id:
            return False
        
        # Check if donor already responded to this request
        # (Would need a DonorResponse model to track this)
        
        return True
