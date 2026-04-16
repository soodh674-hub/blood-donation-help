"""
Blood Request Workflow Service
Handles donor matching, notifications, and request lifecycle management
"""
import logging
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from .models import BloodRequest, RequestResponse

logger = logging.getLogger(__name__)


class BloodRequestWorkflow:
    """Manages complete blood request lifecycle"""
    
    # Blood group compatibility matrix
    BLOOD_COMPATIBILITY = {
        'A+': ['A+', 'A-', 'O+', 'O-'],
        'A-': ['A-', 'O-'],
        'B+': ['B+', 'B-', 'O+', 'O-'],
        'B-': ['B-', 'O-'],
        'AB+': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],  # Universal recipient
        'AB-': ['A-', 'B-', 'AB-', 'O-'],
        'O+': ['O+', 'O-'],
        'O-': ['O-'],  # Universal donor
    }
    
    @staticmethod
    def get_compatible_blood_groups(patient_blood_group):
        """Get list of compatible donor blood groups"""
        return BloodRequestWorkflow.BLOOD_COMPATIBILITY.get(patient_blood_group, [])
    
    @staticmethod
    def find_matching_donors(blood_request, radius_km=50):
        """
        Find donors matching blood request criteria
        Returns list of donors sorted by distance
        """
        from accounts.models import User
        
        # Get compatible blood groups
        compatible_groups = BloodRequestWorkflow.get_compatible_blood_groups(
            blood_request.patient_blood_group
        )
        
        # Find eligible donors
        donors = User.objects.filter(
            user_type='donor',
            is_active=True,
            is_verified=True,
            is_available=True,
            blood_group__in=compatible_groups
        ).exclude(
            # Exclude donors who already responded
            id__in=RequestResponse.objects.filter(
                request=blood_request
            ).values_list('donor_id', flat=True)
        )
        
        # EXCLUDE donors with anonymous_mode enabled
        try:
            from accounts.models import PrivacySettings
            anonymous_user_ids = PrivacySettings.objects.filter(
                anonymous_mode=True
            ).values_list('user_id', flat=True)
            donors = donors.exclude(id__in=anonymous_user_ids)
        except Exception as e:
            logger.warning(f'Could not filter anonymous donors: {str(e)}')
        
        # Filter by distance if location available
        matching_donors = []
        for donor in donors:
            if donor.latitude and donor.longitude:
                # Calculate distance
                distance = BloodRequestWorkflow.calculate_distance(
                    float(blood_request.latitude),
                    float(blood_request.longitude),
                    float(donor.latitude),
                    float(donor.longitude)
                )
                
                if distance <= radius_km:
                    matching_donors.append({
                        'donor': donor,
                        'distance_km': round(distance, 2)
                    })
        
        # Sort by distance
        matching_donors.sort(key=lambda x: x['distance_km'])
        
        logger.info(f"Found {len(matching_donors)} matching donors for request #{blood_request.id}")
        return matching_donors
    
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth's radius in km
        return c * r
    
    @staticmethod
    def notify_matching_donors(blood_request, radius_km=50):
        """
        Send notifications to all matching donors
        Called when request is activated
        """
        from notifications.models import Notification
        
        matching_donors = BloodRequestWorkflow.find_matching_donors(blood_request, radius_km)
        
        notifications_sent = 0
        for donor_data in matching_donors:
            donor = donor_data['donor']
            distance = donor_data['distance_km']
            
            try:
                # Create notification
                Notification.objects.create(
                    user=donor,
                    notification_type='blood_request',
                    title=f'🩸 Urgent: {blood_request.patient_blood_group} Blood Needed',
                    message=f'{blood_request.patient_name} needs {blood_request.required_units} unit(s) of {blood_request.patient_blood_group} blood at {blood_request.hospital_name}, {blood_request.city} ({distance:.1f} km away). Priority: {blood_request.priority.upper()}',
                    priority='high' if blood_request.priority in ['urgent', 'emergency'] else 'medium',
                    related_request=blood_request
                )
                notifications_sent += 1
            except Exception as e:
                logger.error(f"Failed to notify donor {donor.id}: {str(e)}")
        
        logger.info(f"Sent {notifications_sent} notifications for request #{blood_request.id}")
        return notifications_sent
    
    @staticmethod
    def activate_request(blood_request):
        """
        Activate a blood request and notify donors
        Steps 1-6 of workflow
        """
        # Update request status
        blood_request.status = 'active'
        blood_request.activated_at = timezone.now()
        
        # Calculate expiry
        blood_request.expires_at = timezone.now() + timedelta(
            hours=blood_request.auto_expire_hours
        )
        
        # Track status change
        blood_request.add_status_change('active', 'Request activated and donors notified')
        
        blood_request.save()
        
        # Notify matching donors
        notifications_sent = BloodRequestWorkflow.notify_matching_donors(blood_request)
        
        logger.info(f"Request #{blood_request.id} activated with {notifications_sent} donor notifications")
        return blood_request
    
    @staticmethod
    def donor_accept_request(blood_request, donor):
        """
        Donor accepts blood request
        Steps 7-10 of workflow
        """
        # Check if request can accept more donors
        if not blood_request.can_accept_more_donors:
            logger.warning(f"Request #{blood_request.id} cannot accept more donors")
            return None, "Request has reached maximum donor limit"
        
        # Check if donor already responded
        existing_response = RequestResponse.objects.filter(
            request=blood_request,
            donor=donor
        ).first()
        
        if existing_response:
            return None, "You have already responded to this request"
        
        # Create response
        response = RequestResponse.objects.create(
            request=blood_request,
            donor=donor,
            status='interested',
            responded_at=timezone.now()
        )
        
        # Update request status to in-progress if first donor
        if blood_request.fulfilled_units == 0:
            old_status = blood_request.status
            blood_request.status = 'partially_fulfilled'
            blood_request.add_status_change(
                'partially_fulfilled',
                f'First donor ({donor.username}) accepted'
            )
            blood_request.save()
        
        # Notify requester that donor accepted
        try:
            from notifications.models import Notification
            Notification.objects.create(
                user=blood_request.requester,
                notification_type='donor_response',
                title=f'✅ Donor Accepted Your Request',
                message=f'{donor.get_full_name() or donor.username} has accepted your blood request for {blood_request.patient_name}. You can now coordinate the donation.',
                related_request=blood_request,
                priority='high'
            )
        except Exception as e:
            logger.error(f"Failed to notify requester: {str(e)}")
        
        logger.info(f"Donor {donor.id} accepted request #{blood_request.id}")
        return response, "Successfully accepted request"
    
    @staticmethod
    def donor_decline_request(blood_request, donor):
        """Donor declines/ignores blood request"""
        # Check if response exists
        response = RequestResponse.objects.filter(
            request=blood_request,
            donor=donor
        ).first()
        
        if response:
            response.status = 'declined'
            response.save()
            logger.info(f"Donor {donor.id} declined request #{blood_request.id}")
        
        return True
    
    @staticmethod
    def update_donor_status(response, new_status):
        """
        Update donor response status
        Steps 13-14 of workflow
        """
        valid_transitions = {
            'interested': ['en_route', 'unavailable'],
            'en_route': ['arrived', 'unavailable'],
            'arrived': ['donated', 'unavailable'],
        }
        
        current_status = response.status
        if new_status not in valid_transitions.get(current_status, []):
            return False, f"Invalid status transition from {current_status} to {new_status}"
        
        # Update status
        response.status = new_status
        
        # Update timestamps
        if new_status == 'en_route':
            response.en_route_at = timezone.now()
        elif new_status == 'arrived':
            response.arrived_at = timezone.now()
        elif new_status == 'donated':
            response.completed_at = timezone.now()
            
            # Update fulfilled units
            blood_request = response.request
            blood_request.fulfilled_units += 1
            
            # Check if request is fully fulfilled
            if blood_request.fulfilled_units >= blood_request.required_units:
                blood_request.status = 'fulfilled'
                blood_request.add_status_change(
                    'fulfilled',
                    f'Request fulfilled by {response.donor.username}'
                )
            
            blood_request.save()
        
        response.save()
        
        # Notify requester of status change
        try:
            from notifications.models import Notification
            status_messages = {
                'en_route': f'{response.donor.get_full_name() or response.donor.username} is on the way to {response.request.hospital_name}',
                'arrived': f'{response.donor.get_full_name() or response.donor.username} has arrived at the hospital',
                'donated': f'{response.donor.get_full_name() or response.donor.username} has completed the donation! ❤️',
                'unavailable': f'{response.donor.get_full_name() or response.donor.username} is no longer available',
            }
            
            Notification.objects.create(
                user=response.request.requester,
                notification_type='status_update',
                title=f'Donor Status Update',
                message=status_messages.get(new_status, 'Status updated'),
                related_request=response.request,
                priority='high' if new_status == 'donated' else 'medium'
            )
        except Exception as e:
            logger.error(f"Failed to send status notification: {str(e)}")
        
        return True, f"Status updated to {new_status}"
    
    @staticmethod
    def get_donor_contact(response, requesting_user):
        """
        Share contact details between requester and donor
        Step 11 of workflow
        """
        blood_request = response.request
        
        # Allow contact sharing if:
        # 1. User is the requester
        # 2. User is the donor
        # 3. User is admin
        if requesting_user not in [blood_request.requester, response.donor] and not requesting_user.is_staff:
            return None, "Unauthorized to view contact details"
        
        if requesting_user == blood_request.requester:
            # Requester sees donor contact
            return {
                'name': response.donor.get_full_name() or response.donor.username,
                'phone': response.donor.phone_number,
                'email': response.donor.email,
                'blood_group': response.donor.blood_group,
            }, "Contact details retrieved"
        else:
            # Donor sees requester contact
            return {
                'name': blood_request.contact_person,
                'phone': blood_request.contact_phone,
                'email': blood_request.contact_email,
                'hospital': blood_request.hospital_name,
                'address': blood_request.exact_address or f'{blood_request.hospital_name}, {blood_request.city}',
            }, "Contact details retrieved"
    
    @staticmethod
    def expire_request(blood_request):
        """Expire a blood request"""
        blood_request.status = 'expired'
        blood_request.add_status_change('expired', 'Request expired due to time limit')
        blood_request.save()
        
        logger.info(f"Request #{blood_request.id} expired")
    
    @staticmethod
    def cancel_request(blood_request, user, reason=""):
        """
        Cancel a blood request
        Admin or requester can cancel
        """
        if user not in [blood_request.requester, user] and not user.is_staff:
            return False, "Unauthorized to cancel this request"
        
        blood_request.status = 'cancelled'
        blood_request.add_status_change('cancelled', reason or 'Request cancelled')
        blood_request.save()
        
        # Notify all responding donors
        try:
            from notifications.models import Notification
            responses = RequestResponse.objects.filter(
                request=blood_request,
                status__in=['interested', 'en_route', 'arrived']
            )
            
            for response in responses:
                Notification.objects.create(
                    user=response.donor,
                    notification_type='status_update',
                    title=f'❌ Request Cancelled',
                    message=f'The blood request for {blood_request.patient_name} has been cancelled. Reason: {reason or "No longer needed"}',
                    related_request=blood_request,
                    priority='high'
                )
        except Exception as e:
            logger.error(f"Failed to notify donors about cancellation: {str(e)}")
        
        logger.info(f"Request #{blood_request.id} cancelled by {user.username}")
        return True, "Request cancelled successfully"
    
    @staticmethod
    def get_request_history(blood_request):
        """Get complete history of a request"""
        return {
            'request': blood_request,
            'status_history': blood_request.status_history,
            'responses': RequestResponse.objects.filter(
                request=blood_request
            ).select_related('donor').order_by('-responded_at'),
            'total_responses': RequestResponse.objects.filter(
                request=blood_request
            ).count(),
            'accepted_responses': RequestResponse.objects.filter(
                request=blood_request,
                status__in=['interested', 'en_route', 'arrived', 'donated']
            ).count(),
            'completed_donations': RequestResponse.objects.filter(
                request=blood_request,
                status='donated'
            ).count(),
        }
