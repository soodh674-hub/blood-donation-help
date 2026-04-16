"""
Enhanced REST API endpoints for React web and mobile apps
Provides comprehensive data for modern UI
"""
import logging
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from accounts.serializers import UserPublicSerializer
from blood_requests_app.models import BloodRequest, RequestMatch, DonorRating
from blood_requests_app.models_chat import ChatMessage
from blood_requests_app.serializers import (
    BloodRequestSerializer,
    BloodRequestDetailSerializer,
    BloodRequestCreateSerializer,
    ChatMessageSerializer,
    DonorRatingSerializer,
    RequestMatchSerializer
)
from notifications.models import Notification

# Try to import donor models, but don't fail if they don't exist
DonorAvailabilityModel = None
DonorHistory = None
try:
    from donors.models import DonorAvailability, DonorHistory
    DonorAvailabilityModel = DonorAvailability
except ImportError:
    print("ℹ️ Donors app or models not available, donor location features disabled")

logger = logging.getLogger(__name__)


# ==================== DASHBOARD & STATS ====================

class DashboardStatsView(APIView):
    """Get dashboard statistics for homepage"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        try:
            # Calculate stats
            total_lives_saved = DonorHistory.objects.filter(is_successful=True).count()
            total_donors = User.objects.filter(user_type='donor', is_verified=True).count()
            total_requests_fulfilled = BloodRequest.objects.filter(status='fulfilled').count()
            active_requests = BloodRequest.objects.filter(status__in=['active', 'urgent']).count()
            
            return Response({
                'success': True,
                'stats': {
                    'lives_saved': total_lives_saved,
                    'donors_joined': total_donors,
                    'requests_fulfilled': total_requests_fulfilled,
                    'active_requests': active_requests
                }
            })
        except Exception as e:
            logger.error(f'Error fetching dashboard stats: {str(e)}')
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LiveRequestsView(APIView):
    """Get live/active blood requests with location data"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
            blood_group = request.query_params.get('blood_group')
            city = request.query_params.get('city')
            
            # Filter active requests - show ALL for debugging
            queryset = BloodRequest.objects.all().order_by('-created_at')[:limit]
            
            # Optional filters
            if blood_group:
                queryset = queryset.filter(patient_blood_group=blood_group)
            if city:
                queryset = queryset.filter(city__icontains=city)
            
            serializer = BloodRequestSerializer(queryset, many=True)
            
            return Response({
                'success': True,
                'requests': serializer.data,
                'count': len(queryset)
            })
        except Exception as e:
            logger.error(f'Error fetching live requests: {str(e)}')
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== DONOR SEARCH ====================

class DonorSearchView(APIView):
    """Search for available donors by blood group and location"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            blood_group = request.query_params.get('blood_group')
            city = request.query_params.get('city')
            latitude = request.query_params.get('latitude')
            longitude = request.query_params.get('longitude')
            max_distance = float(request.query_params.get('max_distance', 50))

            # Start with verified donors who are available
            donors = User.objects.filter(
                user_type='donor',
                is_available=True
            )

            # Filter by blood group
            if blood_group:
                donors = donors.filter(blood_group=blood_group)

            # Filter by city
            if city:
                donors = donors.filter(city__icontains=city)

            # Get donor list with basic info
            donor_list = []
            for donor in donors[:20]:  # Limit to 20 results
                try:
                    donor_data = {
                        'id': donor.id,
                        'name': donor.get_full_name() or donor.username,
                        'blood_group': donor.blood_group,
                        'city': donor.city,
                        'state': donor.state,
                        'is_available': donor.is_available,
                        'is_verified': getattr(donor, 'is_verified', False),
                    }

                    # Try to get location from DonorAvailabilityModel if it exists
                    if DonorAvailabilityModel:
                        try:
                            availability = DonorAvailabilityModel.objects.get(donor=donor)
                            donor_data['last_updated'] = availability.last_updated

                            # Calculate distance if coordinates provided
                            if latitude and longitude and availability.current_latitude and availability.current_longitude:
                                from math import radians, cos, sin, sqrt, atan2

                                lat1, lon1 = float(latitude), float(longitude)
                                lat2, lon2 = float(availability.current_latitude), float(availability.current_longitude)

                                R = 6371  # Earth radius in km
                                dlat = radians(lat2 - lat1)
                                dlon = radians(lon2 - lon1)
                                a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                                c = 2 * atan2(sqrt(a), sqrt(1-a))
                                distance = round(R * c, 2)

                                if distance <= max_distance:
                                    donor_data['distance_km'] = distance
                                    donor_list.append(donor_data)
                            else:
                                # No distance calculation, add anyway
                                donor_list.append(donor_data)
                        except DonorAvailabilityModel.DoesNotExist:
                            # Model doesn't exist, add donor without location data
                            donor_list.append(donor_data)
                        except Exception:
                            # Any other error with availability model, add donor without location
                            donor_list.append(donor_data)
                    else:
                        # DonorAvailabilityModel not available, add donor without location
                        donor_list.append(donor_data)

                except Exception as e:
                    # Skip this donor if there's an error
                    print(f"ℹ️ Error processing donor {donor.id}: {e}")
                    continue

            return Response({
                'success': True,
                'donors': donor_list,
                'count': len(donor_list)
            })
        except Exception as e:
            logger.error(f'Error searching donors: {str(e)}')
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== REQUEST TRACKING ====================

class TrackRequestView(APIView):
    """Track a specific blood request with all details"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, request_id):
        try:
            blood_request = BloodRequest.objects.select_related('requester').prefetch_related(
                'matches__donor'
            ).get(id=request_id)
            
            serializer = BloodRequestDetailSerializer(blood_request)
            
            return Response({
                'success': True,
                'request': serializer.data
            })
        except BloodRequest.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Request not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f'Error tracking request: {str(e)}')
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== NOTIFICATIONS ====================

class NotificationsView(APIView):
    """Get user notifications"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
            
            notifications = Notification.objects.filter(user=request.user)
            
            if unread_only:
                notifications = notifications.filter(is_read=False)
            
            notifications = notifications.order_by('-created_at')[:50]
            
            data = [{
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'notification_type': n.notification_type,
                'priority': n.priority,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
            } for n in notifications]
            
            unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
            
            return Response({
                'success': True,
                'notifications': data,
                'unread_count': unread_count
            })
        except Exception as e:
            logger.error(f'Error fetching notifications: {str(e)}')
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Mark notification as read"""
        try:
            notification_id = request.data.get('notification_id')
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.mark_as_read()
            
            return Response({
                'success': True,
                'message': 'Notification marked as read'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== CHAT ====================

class ChatMessagesView(APIView):
    """Get chat messages for a blood request"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, request_id):
        try:
            messages = ChatMessage.objects.filter(
                blood_request_id=request_id
            ).select_related('sender').order_by('timestamp')[:100]
            
            serializer = ChatMessageSerializer(messages, many=True)
            
            return Response({
                'success': True,
                'messages': serializer.data
            })
        except Exception as e:
            logger.error(f'Error fetching chat messages: {str(e)}')
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== USER PROFILE ====================

class UserProfileView(APIView):
    """Get current user profile with donation history"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            
            # Get donation history
            donation_history = []
            if DonorHistory:
                try:
                    donation_history = DonorHistory.objects.filter(
                        donor=user
                    ).order_by('-donation_date')[:10]
                except Exception:
                    donation_history = []
            
            history_data = [{
                'id': dh.id,
                'donation_date': dh.donation_date.isoformat(),
                'hospital': dh.hospital,
                'city': dh.city,
                'blood_group': dh.blood_group,
                'is_successful': dh.is_successful,
            } for dh in donation_history]
            
            # Get availability status
            availability_data = None
            if DonorAvailabilityModel:
                try:
                    availability = DonorAvailabilityModel.objects.get(donor=user)
                    availability_data = {
                        'is_available': availability.is_available,
                        'last_updated': availability.last_updated.isoformat(),
                    }
                except DonorAvailabilityModel.DoesNotExist:
                    availability_data = None
            
            return Response({
                'success': True,
                'user': UserPublicSerializer(user).data,
                'donation_history': history_data,
                'availability': availability_data,
                'stats': {
                    'total_donations': len(donation_history),
                    'successful_donations': sum(1 for dh in donation_history if dh.is_successful),
                }
            })
        except Exception as e:
            logger.error(f'Error fetching user profile: {str(e)}')
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== BLOOD REQUEST CRUD ====================

class CreateBloodRequestView(APIView):
    """Create a new blood request"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = BloodRequestCreateSerializer(data=request.data)
            
            if serializer.is_valid():
                blood_request = serializer.save(requester=request.user)
                
                return Response({
                    'success': True,
                    'message': 'Blood request created successfully',
                    'request_id': blood_request.id
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Error creating blood request: {str(e)}')
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MyRequestsView(APIView):
    """Get all requests created by current user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            requests = BloodRequest.objects.filter(
                Q(contact_email=request.user.email) |
                Q(contact_phone=request.user.phone_number) if request.user.phone_number else Q()
            ).order_by('-created_at')
            
            serializer = BloodRequestSerializer(requests, many=True)
            
            return Response({
                'success': True,
                'requests': serializer.data,
                'count': len(requests)
            })
        except Exception as e:
            logger.error(f'Error fetching my requests: {str(e)}')
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
