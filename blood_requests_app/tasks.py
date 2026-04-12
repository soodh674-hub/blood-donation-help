"""
Phase 6: Status Workflow Engine - Celery Tasks
Handles automated status transitions, expiry checks, and notifications
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
import logging

from .models import BloodRequest, RequestResponse
from notifications.models import Notification

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_expired_requests(self):
    """
    Celery task to check and expire old blood requests
    Runs every hour
    
    Status transitions:
    - active/partially_fulfilled + expired → expired
    - Sends notification to requester
    """
    try:
        now = timezone.now()
        
        # Find requests that should be expired
        expired_requests = BloodRequest.objects.filter(
            status__in=['active', 'partially_fulfilled', 'approved'],
            expires_at__lt=now
        ).exclude(
            status='expired'
        )
        
        expired_count = 0
        for request in expired_requests:
            old_status = request.status
            request.status = 'expired'
            request.save(update_fields=['status'])
            
            # Log status change
            logger.info(f"Request #{request.id} expired. Status: {old_status} → expired")
            
            # Send notification to requester
            try:
                Notification.objects.create(
                    user=request.requester,
                    notification_type='request_update',
                    title=f'⏰ Blood Request Expired',
                    message=f'Your blood request for {request.patient_name} at {request.hospital_name} has expired.\n\n'
                           f'Blood Group: {request.patient_blood_group}\n'
                           f'Hospital: {request.hospital_name}\n'
                           f'Expired At: {request.expires_at.strftime("%Y-%m-%d %H:%M")}\n\n'
                           f'If you still need blood, please create a new request.',
                    related_request=request,
                    priority='high'
                )
                logger.info(f"Sent expiry notification to requester of request #{request.id}")
            except Exception as e:
                logger.error(f"Failed to send expiry notification for request #{request.id}: {str(e)}")
            
            expired_count += 1
        
        logger.info(f"Checked expired requests: {expired_count} requests marked as expired")
        return f"{expired_count} requests expired"
        
    except Exception as e:
        logger.error(f"Error in check_expired_requests task: {str(e)}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes


@shared_task(bind=True, max_retries=3)
def send_expiry_warnings(self):
    """
    Celery task to send expiry warnings before requests expire
    Runs every 30 minutes
    
    Warnings sent:
    - 2 hours before expiry (medium priority)
    - 30 minutes before expiry (high priority/urgent)
    """
    try:
        now = timezone.now()
        
        # Calculate warning windows
        two_hours_later = now + timezone.timedelta(hours=2)
        thirty_min_later = now + timezone.timedelta(minutes=30)
        
        warnings_sent = 0
        
        # Check for 2-hour warnings
        two_hour_requests = BloodRequest.objects.filter(
            status__in=['active', 'partially_fulfilled'],
            expires_at__gt=now,
            expires_at__lte=two_hours_later
        ).exclude(
            Q(approval_notes__icontains='2hr_warning_sent') |
            Q(status='expired')
        )
        
        for request in two_hour_requests:
            try:
                Notification.objects.create(
                    user=request.requester,
                    notification_type='expiry_warning',
                    title=f'⚠️ Request Expiring in 2 Hours',
                    message=f'Your blood request for {request.patient_name} will expire in 2 hours.\n\n'
                           f'Blood Group: {request.patient_blood_group}\n'
                           f'Hospital: {request.hospital_name}\n'
                           f'Expires At: {request.expires_at.strftime("%Y-%m-%d %H:%M")}\n\n'
                           f'Consider extending the deadline or creating a new request if needed.',
                    related_request=request,
                    priority='medium'
                )
                
                # Mark as warned (using approval_notes field temporarily)
                request.approval_notes = f"{request.approval_notes} [2hr_warning_sent]"
                request.save(update_fields=['approval_notes'])
                
                warnings_sent += 1
                logger.info(f"Sent 2-hour expiry warning for request #{request.id}")
                
            except Exception as e:
                logger.error(f"Failed to send 2-hour warning for request #{request.id}: {str(e)}")
        
        # Check for 30-minute urgent warnings
        thirty_min_requests = BloodRequest.objects.filter(
            status__in=['active', 'partially_fulfilled'],
            expires_at__gt=now,
            expires_at__lte=thirty_min_later
        ).exclude(
            Q(approval_notes__icontains='30min_warning_sent') |
            Q(status='expired')
        )
        
        for request in thirty_min_requests:
            try:
                Notification.objects.create(
                    user=request.requester,
                    notification_type='expiry_warning',
                    title=f'🚨 URGENT: Request Expiring in 30 Minutes!',
                    message=f'URGENT: Your blood request for {request.patient_name} will expire in 30 minutes!\n\n'
                           f'Blood Group: {request.patient_blood_group}\n'
                           f'Hospital: {request.hospital_name}\n'
                           f'Expires At: {request.expires_at.strftime("%Y-%m-%d %H:%M")}\n\n'
                           f'Please take immediate action. Create a new request if this one expires.',
                    related_request=request,
                    priority='urgent'
                )
                
                # Mark as warned
                request.approval_notes = f"{request.approval_notes} [30min_warning_sent]"
                request.save(update_fields=['approval_notes'])
                
                warnings_sent += 1
                logger.info(f"Sent 30-min URGENT expiry warning for request #{request.id}")
                
            except Exception as e:
                logger.error(f"Failed to send 30-min warning for request #{request.id}: {str(e)}")
        
        logger.info(f"Expiry warnings sent: {warnings_sent} total warnings")
        return f"{warnings_sent} warnings sent"
        
    except Exception as e:
        logger.error(f"Error in send_expiry_warnings task: {str(e)}")
        raise self.retry(exc=e, countdown=300)


@shared_task(bind=True, max_retries=3)
def update_request_status_automatically(self):
    """
    Celery task to automatically update request status based on donor responses
    Runs every 15 minutes
    
    Status transitions:
    - approved + donors responded → active
    - active + all units fulfilled → fulfilled
    - active + some units fulfilled → partially_fulfilled
    """
    try:
        updated_count = 0
        
        # Get all active/approved requests
        active_requests = BloodRequest.objects.filter(
            status__in=['approved', 'active', 'partially_fulfilled']
        ).exclude(
            status='expired'
        )
        
        for request in active_requests:
            old_status = request.status
            new_status = None
            
            # Count completed donations
            donated_count = request.responses.filter(status='donated').count()
            interested_count = request.responses.filter(
                status__in=['interested', 'en_route', 'arrived']
            ).count()
            
            # Logic for status updates
            if request.status == 'approved' and interested_count > 0:
                # First donor responded, activate the request
                new_status = 'active'
                
            elif request.status in ['active', 'partially_fulfilled']:
                if donated_count >= request.required_units:
                    # All units fulfilled
                    new_status = 'fulfilled'
                elif donated_count > 0:
                    # Some units fulfilled
                    new_status = 'partially_fulfilled'
            
            # Update status if changed
            if new_status and new_status != old_status:
                request.status = new_status
                request.save(update_fields=['status'])
                
                logger.info(f"Request #{request.id} status updated: {old_status} → {new_status}")
                
                # Send notification about status change
                try:
                    status_messages = {
                        'active': f'✅ Your blood request is now ACTIVE! Donors are being notified.',
                        'partially_fulfilled': f'🎉 Great progress! {donated_count}/{request.required_units} units fulfilled.',
                        'fulfilled': f'🎊 SUCCESS! All {request.required_units} units have been fulfilled. Thank you to all donors!'
                    }
                    
                    if new_status in status_messages:
                        Notification.objects.create(
                            user=request.requester,
                            notification_type='request_update',
                            title=f'Request Status Updated: {new_status.replace("_", " ").title()}',
                            message=f'{status_messages[new_status]}\n\n'
                                   f'Patient: {request.patient_name}\n'
                                   f'Blood Group: {request.patient_blood_group}\n'
                                   f'Hospital: {request.hospital_name}',
                            related_request=request,
                            priority='high' if new_status == 'fulfilled' else 'medium'
                        )
                except Exception as e:
                    logger.error(f"Failed to send status update notification for request #{request.id}: {str(e)}")
                
                updated_count += 1
        
        logger.info(f"Automatic status updates: {updated_count} requests updated")
        return f"{updated_count} status updates"
        
    except Exception as e:
        logger.error(f"Error in update_request_status_automatically task: {str(e)}")
        raise self.retry(exc=e, countdown=300)


@shared_task(bind=True, max_retries=3)
def cleanup_old_completed_requests(self, days_old=30):
    """
    Celery task to archive/cleanup very old completed requests
    Runs daily at midnight
    
    Archives requests that are:
    - Status: fulfilled/cancelled/expired
    - Older than specified days (default 30)
    """
    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
        
        old_requests = BloodRequest.objects.filter(
            status__in=['fulfilled', 'cancelled', 'expired'],
            updated_at__lt=cutoff_date
        )
        
        archived_count = old_requests.count()
        
        # For now, just log them (could implement actual archival later)
        logger.info(f"Found {archived_count} old completed requests older than {days_old} days")
        
        # Optional: Add 'archived' status or move to separate table
        # For now, we'll just leave them in database but mark them
        
        return f"{archived_count} old requests identified for archival"
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_completed_requests task: {str(e)}")
        raise self.retry(exc=e, countdown=600)


@shared_task(bind=True, max_retries=3)
def notify_donors_of_nearby_emergency(self):
    """
    Celery task to find and notify donors about nearby emergency requests
    Runs every 10 minutes during peak hours
    
    Finds:
    - Emergency/urgent requests within 10km of available donors
    - Sends push notifications to matching donors
    """
    try:
        from notifications.services import BloodRequestNotificationService
        
        # Get active emergency/urgent requests
        urgent_requests = BloodRequest.objects.filter(
            status__in=['active', 'partially_fulfilled'],
            priority__in=['emergency', 'urgent'],
            expires_at__gt=timezone.now()
        )
        
        notified_count = 0
        for request in urgent_requests:
            try:
                # Use existing notification service
                count = BloodRequestNotificationService.send_blood_request_notification(
                    blood_request=request,
                    limit=20  # Limit to closest 20 donors for urgent requests
                )
                notified_count += count
                logger.info(f"Notified {count} donors about emergency request #{request.id}")
            except Exception as e:
                logger.error(f"Failed to notify donors for request #{request.id}: {str(e)}")
        
        logger.info(f"Emergency notifications sent: {notified_count} total donors notified")
        return f"{notified_count} donors notified"
        
    except Exception as e:
        logger.error(f"Error in notify_donors_of_nearby_emergency task: {str(e)}")
        raise self.retry(exc=e, countdown=300)


# ============================================================================
# STATUS TRANSITION HELPER FUNCTIONS
# ============================================================================

def transition_request_status(request, new_status, reason="", performed_by=None):
    """
    Helper function to safely transition request status with validation
    
    Args:
        request: BloodRequest instance
        new_status: Target status string
        reason: Reason for status change
        performed_by: User who initiated the change
    
    Returns:
        bool: True if transition successful, False otherwise
    """
    valid_transitions = {
        'pending': ['approved', 'cancelled'],
        'approved': ['active', 'cancelled'],
        'active': ['partially_fulfilled', 'fulfilled', 'cancelled', 'expired'],
        'partially_fulfilled': ['fulfilled', 'cancelled', 'expired', 'active'],
        'fulfilled': [],  # Terminal state
        'cancelled': [],  # Terminal state
        'expired': ['active'],  # Can be reactivated
    }
    
    current_status = request.status
    
    # Validate transition
    if new_status not in valid_transitions.get(current_status, []):
        logger.warning(f"Invalid status transition: {current_status} → {new_status} for request #{request.id}")
        return False
    
    # Perform transition
    old_status = request.status
    request.status = new_status
    
    if reason:
        request.approval_notes = f"{request.approval_notes} [{new_status}: {reason}]"
    
    request.save(update_fields=['status', 'approval_notes'])
    
    logger.info(f"Request #{request.id} status: {old_status} → {new_status} (Reason: {reason})")
    
    return True
