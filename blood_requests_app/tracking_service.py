"""
Live Donor Location Tracking Service
Handles real-time GPS location updates, ETA calculations, and route history
"""
import logging
from django.utils import timezone
from datetime import timedelta
import math

logger = logging.getLogger(__name__)


class DonorLocationTracker:
    """Manages real-time donor location tracking"""
    
    @staticmethod
    def update_donor_location(response, latitude, longitude, accuracy=None):
        """
        Update donor's current location
        Creates location history entry
        """
        from blood_requests_app.models import DonorLocationHistory, RequestResponse
        
        # Update response location
        response.donor_latitude = latitude
        response.donor_longitude = longitude
        response.last_location_update = timezone.now()
        response.save(update_fields=['donor_latitude', 'donor_longitude', 'last_location_update'])
        
        # Create location history entry
        location_entry = DonorLocationHistory.objects.create(
            donor=response.donor,
            request=response.request,
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy
        )
        
        logger.info(f"Location updated for donor {response.donor.id}: ({latitude}, {longitude})")
        return location_entry
    
    @staticmethod
    def calculate_eta(donor_lat, donor_lng, hospital_lat, hospital_lng, avg_speed_kmh=40):
        """
        Calculate estimated time of arrival
        Returns minutes
        """
        distance = DonorLocationTracker.calculate_distance(
            donor_lat, donor_lng,
            hospital_lat, hospital_lng
        )
        
        # ETA = Distance / Speed
        eta_hours = distance / avg_speed_kmh
        eta_minutes = eta_hours * 60
        
        return {
            'distance_km': round(distance, 2),
            'eta_minutes': round(eta_minutes),
            'eta_text': DonorLocationTracker.format_eta(eta_minutes),
            'arrival_time': (timezone.now() + timedelta(minutes=eta_minutes)).isoformat()
        }
    
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance using Haversine formula (km)"""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    @staticmethod
    def format_eta(minutes):
        """Format ETA to human-readable text"""
        if minutes < 1:
            return "Arriving now"
        elif minutes < 60:
            return f"{int(minutes)} min"
        else:
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            return f"{hours}h {mins}m"
    
    @staticmethod
    def get_donor_route_history(response, limit=50):
        """Get donor's location history for route tracking"""
        from blood_requests_app.models import DonorLocationHistory
        
        history = DonorLocationHistory.objects.filter(
            donor=response.donor,
            request=response.request
        ).order_by('-timestamp')[:limit]
        
        return [
            {
                'latitude': float(h.latitude),
                'longitude': float(h.longitude),
                'timestamp': h.timestamp.isoformat(),
                'accuracy': h.accuracy_meters
            }
            for h in history
        ]
    
    @staticmethod
    def get_live_tracking_data(request_id):
        """Get complete live tracking data for all donors"""
        from blood_requests_app.models import BloodRequest, RequestResponse
        
        try:
            blood_request = BloodRequest.objects.get(id=request_id)
        except BloodRequest.DoesNotExist:
            return None
        
        responses = RequestResponse.objects.filter(
            request=blood_request,
            status__in=['interested', 'en_route', 'arrived'],
            donor_latitude__isnull=False,
            donor_longitude__isnull=False
        ).select_related('donor')
        
        tracking_data = {
            'request_id': request_id,
            'hospital': {
                'latitude': float(blood_request.latitude),
                'longitude': float(blood_request.longitude),
                'name': blood_request.hospital_name
            },
            'donors': [],
            'timestamp': timezone.now().isoformat()
        }
        
        for response in responses:
            # Calculate ETA
            eta_data = DonorLocationTracker.calculate_eta(
                float(response.donor_latitude),
                float(response.donor_longitude),
                float(blood_request.latitude),
                float(blood_request.longitude)
            )
            
            # Get route history
            route = DonorLocationTracker.get_donor_route_history(response, limit=20)
            
            donor_data = {
                'response_id': response.id,
                'donor_id': response.donor.id,
                'name': response.donor.get_full_name() or response.donor.username,
                'phone': response.donor.phone_number,
                'blood_group': response.donor.blood_group,
                'status': response.status,
                'location': {
                    'latitude': float(response.donor_latitude),
                    'longitude': float(response.donor_longitude),
                    'last_update': response.last_location_update.isoformat() if response.last_location_update else None
                },
                'eta': eta_data,
                'route_history': route,
                'distance_km': eta_data['distance_km'],
                'is_selected': response.is_selected
            }
            
            tracking_data['donors'].append(donor_data)
        
        return tracking_data
    
    @staticmethod
    def check_proximity_alerts(response, hospital_lat, hospital_lng, radius_km=1):
        """Check if donor is near hospital and trigger alerts"""
        if not response.donor_latitude or not response.donor_longitude:
            return False
        
        distance = DonorLocationTracker.calculate_distance(
            float(response.donor_latitude),
            float(response.donor_longitude),
            hospital_lat,
            hospital_lng
        )
        
        if distance <= radius_km and response.status == 'en_route':
            # Donor is near hospital
            return True
        
        return False
